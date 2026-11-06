from fastapi import APIRouter

from app.api.v1 import (
    admin,
    analytics,
    arena,
    auth,
    classes,
    events,
    homework,
    notices,
    parent,
    parent_profile,
    pets,
    practice,
    problems,
    student_profile,
    suggestions,
    teacher_profile,
    teacher_roster,
    user_notifications,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(classes.router)
api_router.include_router(teacher_roster.router)
api_router.include_router(problems.router)
api_router.include_router(homework.router)
api_router.include_router(practice.router)
api_router.include_router(student_profile.router)
api_router.include_router(pets.router)
api_router.include_router(arena.router)
api_router.include_router(suggestions.router)
api_router.include_router(analytics.router)
api_router.include_router(parent.router)
api_router.include_router(teacher_profile.router)
api_router.include_router(parent_profile.router)
api_router.include_router(events.router)
api_router.include_router(notices.router)
api_router.include_router(user_notifications.router)
