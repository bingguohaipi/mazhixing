from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.roster_schema import EnrollStudentsRequest
from app.schemas.class_schema import (
    AssignStudentGroupRequest,
    BindParentRequest,
    BindParentResponse,
    ClassCreateRequest,
    ClassDetail,
    ClassListItem,
    ClassStudentItem,
    ClassUpdateRequest,
    ParentBindingItem,
    StudentCreateRequest,
    StudentCreateResponse,
    StudentGroupCreateRequest,
    StudentGroupItem,
    StudentGroupUpdateRequest,
    StudentUpdateRequest,
)
from app.services.class_service import ClassService

router = APIRouter(prefix="/classes", tags=["班级管理"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.TEACHER))]


def get_class_service(db: Annotated[Session, Depends(get_db)]) -> ClassService:
    return ClassService(db)


@router.get("", response_model=ApiResponse[list[ClassListItem]])
def list_classes(
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
    keyword: str | None = Query(None, max_length=64),
    weekday: str | None = Query(None, max_length=8, description="周几，如：周六"),
    course_type: str | None = Query(None, max_length=64, description="编程语言：Python 或 C++"),
):
    items = service.list_classes(
        current_user.id,
        keyword,
        weekday=weekday,
        course_type=course_type,
    )
    return success(items)


@router.post("", response_model=ApiResponse[ClassDetail])
def create_class(
    payload: ClassCreateRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    item = service.create_class(current_user.id, payload)
    return success(item, message="班级创建成功")


@router.get("/{class_id}", response_model=ApiResponse[ClassDetail])
def get_class(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    item = service.get_class(class_id, current_user.id)
    return success(item)


@router.put("/{class_id}", response_model=ApiResponse[ClassDetail])
def update_class(
    class_id: int,
    payload: ClassUpdateRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    item = service.update_class(class_id, current_user.id, payload)
    return success(item, message="班级更新成功")


@router.delete("/{class_id}", response_model=ApiResponse[None])
def delete_class(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    service.delete_class(class_id, current_user.id)
    return success(message="班级已删除")


@router.get("/{class_id}/students", response_model=ApiResponse[list[ClassStudentItem]])
def list_students(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
    keyword: str | None = Query(None, max_length=64),
):
    items = service.list_students(class_id, current_user.id, keyword)
    return success(items)


@router.post("/{class_id}/students", response_model=ApiResponse[StudentCreateResponse])
def add_student(
    class_id: int,
    payload: StudentCreateRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    result = service.add_student(class_id, current_user.id, payload)
    return success(result, message="学生添加成功")


@router.post("/{class_id}/students/enroll", response_model=ApiResponse[list[ClassStudentItem]])
def enroll_students(
    class_id: int,
    payload: EnrollStudentsRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    items = service.enroll_students(class_id, current_user.id, payload.student_ids)
    return success(items, message="学生已加入班级")


@router.put("/{class_id}/students/{student_id}", response_model=ApiResponse[ClassStudentItem])
def update_student(
    class_id: int,
    student_id: int,
    payload: StudentUpdateRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    item = service.update_student(class_id, student_id, current_user.id, payload)
    return success(item, message="学生信息已更新")


@router.delete("/{class_id}/students/{student_id}", response_model=ApiResponse[None])
def remove_student(
    class_id: int,
    student_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    service.remove_student(class_id, student_id, current_user.id)
    return success(message="学生已从班级移除")


@router.post("/{class_id}/students/{student_id}/reset-password", response_model=ApiResponse[dict])
def reset_student_password(
    class_id: int,
    student_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    password = service.reset_student_password(class_id, student_id, current_user.id)
    return success({"default_password": password}, message="密码已重置")


@router.get(
    "/{class_id}/students/{student_id}/parent-bindings",
    response_model=ApiResponse[list[ParentBindingItem]],
)
def list_parent_bindings(
    class_id: int,
    student_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    items = service.list_parent_bindings(class_id, student_id, current_user.id)
    return success(items)


@router.post(
    "/{class_id}/students/{student_id}/bind-parent",
    response_model=ApiResponse[BindParentResponse],
)
def bind_parent(
    class_id: int,
    student_id: int,
    payload: BindParentRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    result = service.bind_parent(class_id, student_id, current_user.id, payload)
    return success(result, message="家长绑定成功")


@router.get("/{class_id}/groups", response_model=ApiResponse[list[StudentGroupItem]])
def list_groups(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    items = service.list_groups(class_id, current_user.id)
    return success(items)


@router.post("/{class_id}/groups", response_model=ApiResponse[StudentGroupItem])
def create_group(
    class_id: int,
    payload: StudentGroupCreateRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    item = service.create_group(class_id, current_user.id, payload)
    return success(item, message="分组创建成功")


@router.put("/{class_id}/groups/{group_id}", response_model=ApiResponse[StudentGroupItem])
def update_group(
    class_id: int,
    group_id: int,
    payload: StudentGroupUpdateRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    item = service.update_group(class_id, group_id, current_user.id, payload)
    return success(item, message="分组已更新")


@router.delete("/{class_id}/groups/{group_id}", response_model=ApiResponse[None])
def delete_group(
    class_id: int,
    group_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    service.delete_group(class_id, group_id, current_user.id)
    return success(message="分组已删除")


@router.put("/{class_id}/students/{student_id}/group", response_model=ApiResponse[ClassStudentItem])
def assign_student_group(
    class_id: int,
    student_id: int,
    payload: AssignStudentGroupRequest,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    item = service.assign_student_group(class_id, student_id, current_user.id, payload)
    return success(item, message="分组已更新")


@router.delete("/{class_id}/students/{student_id}/bind-parent/{parent_id}", response_model=ApiResponse[None])
def unbind_parent(
    class_id: int,
    student_id: int,
    parent_id: int,
    current_user: TeacherUser,
    service: Annotated[ClassService, Depends(get_class_service)],
):
    service.unbind_parent(class_id, student_id, parent_id, current_user.id)
    return success(message="已解除绑定")
