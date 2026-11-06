"""Run lightweight schema migrations for dev SQLite databases."""

from sqlalchemy import inspect, text

from app.db.session import engine


def run_migrations() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    with engine.begin() as conn:
        if "student_no" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN student_no VARCHAR(32)"))
        if "created_by_teacher_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN created_by_teacher_id INTEGER"))
        if "token_version" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"))

    if inspector.has_table("submissions"):
        submission_columns = {col["name"] for col in inspector.get_columns("submissions")}
        with engine.begin() as conn:
            if "ai_analysis" not in submission_columns:
                conn.execute(text("ALTER TABLE submissions ADD COLUMN ai_analysis TEXT"))

    if inspector.has_table("class_students"):
        enrollment_columns = {col["name"] for col in inspector.get_columns("class_students")}
        with engine.begin() as conn:
            if "group_id" not in enrollment_columns:
                conn.execute(text("ALTER TABLE class_students ADD COLUMN group_id INTEGER"))

    if inspector.has_table("homeworks"):
        homework_columns = {col["name"] for col in inspector.get_columns("homeworks")}
        with engine.begin() as conn:
            if "content_updated_at" not in homework_columns:
                conn.execute(text("ALTER TABLE homeworks ADD COLUMN content_updated_at DATETIME"))

    if inspector.has_table("problems"):
        problem_columns = {col["name"] for col in inspector.get_columns("problems")}
        with engine.begin() as conn:
            if "scope" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN scope VARCHAR(16) NOT NULL DEFAULT 'private'"))
            if "publish_status" not in problem_columns:
                conn.execute(
                    text(
                        "ALTER TABLE problems ADD COLUMN publish_status VARCHAR(16) NOT NULL DEFAULT 'published'"
                    )
                )
            if "public_group_id" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN public_group_id INTEGER"))
            if "version" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN version INTEGER NOT NULL DEFAULT 1"))
            if "arena_enabled" not in problem_columns:
                conn.execute(
                    text("ALTER TABLE problems ADD COLUMN arena_enabled BOOLEAN NOT NULL DEFAULT 0")
                )
            if "arena_opened_at" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN arena_opened_at DATETIME"))
            if "knowledge_points" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN knowledge_points JSON"))
                conn.execute(
                    text(
                        "UPDATE problems SET knowledge_points = json_array(knowledge_point) "
                        "WHERE knowledge_point IS NOT NULL AND trim(knowledge_point) != ''"
                    )
                )
            if "languages" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN languages JSON"))
                conn.execute(
                    text(
                        "UPDATE problems SET languages = json_array("
                        "CASE language WHEN 'Python' THEN 'Python' WHEN 'C++' THEN 'C++' ELSE language END)"
                    )
                )
            if "private_no" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN private_no INTEGER"))
                rows = conn.execute(
                    text(
                        "SELECT id, teacher_id FROM problems "
                        "WHERE scope = 'private' AND deleted_at IS NULL "
                        "ORDER BY teacher_id ASC, id ASC"
                    )
                ).fetchall()
                counters: dict[int, int] = {}
                for row in rows:
                    teacher_id = int(row[1])
                    counters[teacher_id] = counters.get(teacher_id, 0) + 1
                    conn.execute(
                        text("UPDATE problems SET private_no = :no WHERE id = :id"),
                        {"no": counters[teacher_id], "id": int(row[0])},
                    )

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    with engine.begin() as conn:
        if "arena_ranking_opt_out" not in user_columns:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN arena_ranking_opt_out BOOLEAN NOT NULL DEFAULT 0")
            )
        if "arena_agreed_at" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN arena_agreed_at DATETIME"))
        if "avatar_path" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_path VARCHAR(255)"))
        if "nickname" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN nickname VARCHAR(32)"))

    if inspector.has_table("submissions"):
        submission_columns = {col["name"] for col in inspector.get_columns("submissions")}
        with engine.begin() as conn:
            if "arena_session_id" not in submission_columns:
                conn.execute(text("ALTER TABLE submissions ADD COLUMN arena_session_id INTEGER"))

    if inspector.has_table("student_pets"):
        pet_columns = {col["name"] for col in inspector.get_columns("student_pets")}
        with engine.begin() as conn:
            if "last_play_at" not in pet_columns:
                conn.execute(text("ALTER TABLE student_pets ADD COLUMN last_play_at DATETIME"))

    if not inspector.has_table("notice_reads"):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE notice_reads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notice_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        read_at DATETIME NOT NULL DEFAULT (datetime('now')),
                        FOREIGN KEY(notice_id) REFERENCES notices(id),
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        UNIQUE(notice_id, user_id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX idx_notice_reads_notice_id ON notice_reads (notice_id)"))
            conn.execute(text("CREATE INDEX idx_notice_reads_user_id ON notice_reads (user_id)"))

    if inspector.has_table("suggestions"):
        suggestion_columns = {col["name"] for col in inspector.get_columns("suggestions")}
        with engine.begin() as conn:
            if "title" not in suggestion_columns:
                conn.execute(text("ALTER TABLE suggestions ADD COLUMN title VARCHAR(200) NOT NULL DEFAULT ''"))
                conn.execute(
                    text(
                        "UPDATE suggestions SET title = trim(substr(content, 1, 200)) "
                        "WHERE title IS NULL OR title = ''"
                    )
                )
            if "satisfaction_rating" not in suggestion_columns:
                conn.execute(text("ALTER TABLE suggestions ADD COLUMN satisfaction_rating INTEGER"))

    if not inspector.has_table("suggestion_replies"):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE suggestion_replies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suggestion_id INTEGER NOT NULL,
                        from_user_id INTEGER NOT NULL,
                        content TEXT NOT NULL DEFAULT '',
                        image_urls TEXT,
                        created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                        updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
                        FOREIGN KEY(suggestion_id) REFERENCES suggestions(id),
                        FOREIGN KEY(from_user_id) REFERENCES users(id)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX idx_suggestion_replies_suggestion_id ON suggestion_replies (suggestion_id)")
            )

    if inspector.has_table("problems"):
        problem_columns = {col["name"] for col in inspector.get_columns("problems")}
        with engine.begin() as conn:
            if "image_urls" not in problem_columns:
                conn.execute(text("ALTER TABLE problems ADD COLUMN image_urls JSON"))

    if inspector.has_table("verification_codes"):
        verification_columns = {col["name"] for col in inspector.get_columns("verification_codes")}
        with engine.begin() as conn:
            if "out_id" not in verification_columns:
                conn.execute(text("ALTER TABLE verification_codes ADD COLUMN out_id VARCHAR(64)"))
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_verification_codes_out_id ON verification_codes (out_id)")
                )
