"""Tests for admin, public problems, and suggestions."""

from app.core.security import hash_password
from app.models.audit import ParentStudentBinding
from app.models.problem import ProblemScope, PublicPublishStatus, TestCase
from app.models.user import User, UserRole
from tests.conftest import auth_header


def test_admin_public_problem_and_student_practice(client, db, teacher, student, teaching_class):
    admin = User(
        account="admin_test",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="Admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    admin_headers = {
        "Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'account': 'admin_test', 'password': 'Admin123', 'role': 'admin'}).json()['data']['tokens']['access_token']}"
    }

    create_resp = client.post(
        "/api/v1/admin/public-problems",
        headers=admin_headers,
        json={
            "title": "Sum Two",
            "description": "输出 1+1",
            "languages": ["C++"],
            "difficulty": "入门",
            "gesp_level": "GESP1",
            "knowledge_points": ["数学"],
            "test_cases": [{"input_data": "1", "expected_output": "2", "is_sample": True, "sort_order": 0}],
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    problem_id = create_resp.json()["data"]["id"]

    pub = client.post(f"/api/v1/admin/public-problems/{problem_id}/publish", headers=admin_headers)
    assert pub.status_code == 200

    major_edit = client.put(
        f"/api/v1/admin/public-problems/{problem_id}",
        headers=admin_headers,
        json={"description": "输出 1+1 更新描述", "test_cases": [{"input_data": "1", "expected_output": "2", "is_sample": True, "sort_order": 0}]},
    )
    assert major_edit.status_code == 200, major_edit.text

    student_headers = {
        "Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'account': student.account, 'password': '123456', 'role': 'student'}).json()['data']['tokens']['access_token']}"
    }
    listing = client.get("/api/v1/practice/problems", headers=student_headers)
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] >= 1

    teacher_headers = {
        "Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'account': teacher.account, 'password': 'Teacher123', 'role': 'teacher'}).json()['data']['tokens']['access_token']}"
    }
    catalog = client.get("/api/v1/problems/public/catalog", headers=teacher_headers)
    assert catalog.status_code == 200
    assert any(item["id"] == problem_id for item in catalog.json()["data"]["items"])

    teacher_detail = client.get(f"/api/v1/practice/problems/{problem_id}", headers=teacher_headers)
    assert teacher_detail.status_code == 200, teacher_detail.text
    assert teacher_detail.json()["data"]["title"] == "Sum Two"


def test_admin_delete_old_public_problem_version(client, db):
    admin = User(
        account="admin_del_ver",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="AdminDel",
    )
    db.add(admin)
    db.commit()

    admin_headers = {
        "Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'account': 'admin_del_ver', 'password': 'Admin123', 'role': 'admin'}).json()['data']['tokens']['access_token']}"
    }

    create_resp = client.post(
        "/api/v1/admin/public-problems",
        headers=admin_headers,
        json={
            "title": "Versioned",
            "description": "v1",
            "languages": ["C++"],
            "difficulty": "入门",
            "gesp_level": "GESP1",
            "knowledge_points": ["枚举"],
            "test_cases": [{"input_data": "1", "expected_output": "1", "is_sample": True, "sort_order": 0}],
        },
    )
    assert create_resp.status_code == 200
    v1_id = create_resp.json()["data"]["id"]
    client.post(f"/api/v1/admin/public-problems/{v1_id}/publish", headers=admin_headers)

    new_ver = client.post(f"/api/v1/admin/public-problems/{v1_id}/new-version", headers=admin_headers)
    assert new_ver.status_code == 200
    v2_id = new_ver.json()["data"]["id"]
    client.post(f"/api/v1/admin/public-problems/{v2_id}/publish", headers=admin_headers)

    ok_latest = client.delete(f"/api/v1/admin/public-problems/{v2_id}", headers=admin_headers)
    assert ok_latest.status_code == 200, ok_latest.text

    ok = client.delete(f"/api/v1/admin/public-problems/{v1_id}", headers=admin_headers)
    assert ok.status_code == 200, ok.text

    listing = client.get("/api/v1/admin/public-problems", headers=admin_headers)
    ids = {item["id"] for item in listing.json()["data"]["items"]}
    assert v1_id not in ids
    assert v2_id not in ids


def test_suggestion_between_roles(client, db, teacher, student, teaching_class):
    admin = User(
        account="admin2",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="Admin2",
    )
    db.add(admin)
    db.commit()

    student_token = client.post(
        "/api/v1/auth/login",
        json={"account": student.account, "password": "123456", "role": "student"},
    ).json()["data"]["tokens"]["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    recipients = client.get("/api/v1/suggestions/recipients", headers=student_headers)
    assert recipients.status_code == 200
    ids = {item["id"] for item in recipients.json()["data"]}
    assert teacher.id in ids
    assert admin.id in ids

    create = client.post(
        "/api/v1/suggestions",
        headers=student_headers,
        json={"to_user_id": teacher.id, "content": "题目描述可以更清楚一些", "context_type": "general"},
    )
    assert create.status_code == 200

    teacher_headers = {
        "Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'account': teacher.account, 'password': 'Teacher123', 'role': 'teacher'}).json()['data']['tokens']['access_token']}"
    }
    inbox = client.get("/api/v1/suggestions/inbox", headers=teacher_headers)
    assert inbox.json()["data"]["total"] >= 1
    suggestion_id = inbox.json()["data"]["items"][0]["id"]

    reply = client.post(
        f"/api/v1/suggestions/{suggestion_id}/replies",
        headers=teacher_headers,
        json={"content": "感谢反馈，我们会优化描述", "image_urls": []},
    )
    assert reply.status_code == 200

    inbox_after = client.get("/api/v1/suggestions/inbox", headers=teacher_headers)
    first = inbox_after.json()["data"]["items"][0]
    assert len(first.get("replies", [])) >= 1

    sent = client.get("/api/v1/suggestions/sent", headers=student_headers)
    assert sent.json()["data"]["items"][0]["replies"][0]["content"].startswith("感谢反馈")


def test_suggestion_resolved_rating_and_no_reply(client, db, teacher, student, teaching_class):
    student_headers = auth_header(client, student.account, "123456", "student")
    teacher_headers = auth_header(client, teacher.account, "Teacher123", "teacher")

    create = client.post(
        "/api/v1/suggestions",
        headers=student_headers,
        json={
            "to_user_id": teacher.id,
            "title": "测试评分",
            "content": "请优化说明",
            "context_type": "general",
        },
    )
    assert create.status_code == 200
    suggestion_id = create.json()["data"]["id"]

    resolved = client.patch(
        f"/api/v1/suggestions/{suggestion_id}/status",
        headers=teacher_headers,
        json={"status": "resolved"},
    )
    assert resolved.status_code == 200

    blocked = client.post(
        f"/api/v1/suggestions/{suggestion_id}/replies",
        headers=teacher_headers,
        json={"content": "不应再回复", "image_urls": []},
    )
    assert blocked.status_code == 400

    rated = client.post(
        f"/api/v1/suggestions/{suggestion_id}/rating",
        headers=student_headers,
        json={"score": 4},
    )
    assert rated.status_code == 200
    assert rated.json()["data"]["satisfaction_rating"] == 4

    duplicate = client.post(
        f"/api/v1/suggestions/{suggestion_id}/rating",
        headers=student_headers,
        json={"score": 5},
    )
    assert duplicate.status_code == 400

    forbidden = client.post(
        f"/api/v1/suggestions/{suggestion_id}/rating",
        headers=teacher_headers,
        json={"score": 5},
    )
    assert forbidden.status_code == 403


def test_suggestion_resolved_notifies_sender(client, db, teacher, student, teaching_class):
    student_headers = auth_header(client, student.account, "123456", "student")
    teacher_headers = auth_header(client, teacher.account, "Teacher123", "teacher")

    create = client.post(
        "/api/v1/suggestions",
        headers=student_headers,
        json={"to_user_id": teacher.id, "content": "请优化样例说明", "context_type": "general"},
    )
    assert create.status_code == 200
    suggestion_id = create.json()["data"]["id"]

    resolved = client.patch(
        f"/api/v1/suggestions/{suggestion_id}/status",
        headers=teacher_headers,
        json={"status": "resolved"},
    )
    assert resolved.status_code == 200

    notes = client.get(
        "/api/v1/user-notifications",
        headers=student_headers,
        params={"unread_only": True, "event_key": "suggestion_resolved"},
    )
    assert notes.status_code == 200
    items = notes.json()["data"]["items"]
    assert len(items) >= 1
    assert items[0]["title"] == "建议已处理"


def test_suggestion_recipient_scope_by_role(
    client,
    db,
    teacher,
    student,
    teaching_class,
):
    admin = User(
        account="admin_scope",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="AdminScope",
    )
    other_teacher = User(
        account="13900139001",
        password_hash=hash_password("Teacher123"),
        role=UserRole.TEACHER,
        display_name="其他教师",
    )
    parent = User(
        account="13900139002",
        phone="13900139002",
        password_hash=hash_password("Parent123"),
        role=UserRole.PARENT,
        display_name="测试家长",
    )
    db.add_all([admin, other_teacher, parent])
    db.flush()
    db.add(ParentStudentBinding(parent_id=parent.id, student_id=student.id))
    db.commit()

    def login_headers(account: str, password: str, role: str) -> dict[str, str]:
        token = client.post(
            "/api/v1/auth/login",
            json={"account": account, "password": password, "role": role},
        ).json()["data"]["tokens"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    student_headers = login_headers(student.account, "123456", "student")
    student_recipient_ids = {
        item["id"]
        for item in client.get("/api/v1/suggestions/recipients", headers=student_headers).json()["data"]
    }
    assert teacher.id in student_recipient_ids
    assert admin.id in student_recipient_ids
    assert parent.id not in student_recipient_ids
    assert other_teacher.id not in student_recipient_ids

    teacher_headers = login_headers(teacher.account, "Teacher123", "teacher")
    teacher_recipient_ids = {
        item["id"]
        for item in client.get("/api/v1/suggestions/recipients", headers=teacher_headers).json()["data"]
    }
    assert student.id in teacher_recipient_ids
    assert parent.id in teacher_recipient_ids
    assert admin.id in teacher_recipient_ids
    assert other_teacher.id not in teacher_recipient_ids

    parent_headers = login_headers(parent.account, "Parent123", "parent")
    parent_recipient_ids = {
        item["id"]
        for item in client.get("/api/v1/suggestions/recipients", headers=parent_headers).json()["data"]
    }
    assert teacher.id in parent_recipient_ids
    assert admin.id in parent_recipient_ids
    assert student.id not in parent_recipient_ids

    forbidden = client.post(
        "/api/v1/suggestions",
        headers=student_headers,
        json={"to_user_id": parent.id, "content": "不应成功", "context_type": "general"},
    )
    assert forbidden.status_code == 403


def test_teacher_feedback_on_public_problem(
    client,
    db,
    teacher,
    problem,
) -> None:
    admin = User(
        account="admin_pub_fb",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="AdminPubFb",
    )
    db.add(admin)
    db.commit()

    teacher_headers = auth_header(client, teacher.account, "Teacher123", "teacher")

    detail = client.get(f"/api/v1/practice/problems/{problem.id}", headers=teacher_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["is_public_catalog"] is True

    recipients = client.get(
        "/api/v1/suggestions/recipients",
        headers=teacher_headers,
        params={"context_type": "problem", "context_id": problem.id},
    )
    assert recipients.status_code == 200, recipients.text
    recipient_rows = recipients.json()["data"]
    recipient_ids = {row["id"] for row in recipient_rows}
    assert admin.id in recipient_ids
    assert recipient_rows[0]["id"] == admin.id

    created = client.post(
        "/api/v1/suggestions",
        headers=teacher_headers,
        json={
            "to_user_id": admin.id,
            "content": "【反馈类型】题目描述不清\n\n样例说明可再详细一些",
            "context_type": "problem",
            "context_id": problem.id,
        },
    )
    assert created.status_code == 200, created.text
