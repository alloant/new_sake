from fastapi import APIRouter
from app.views import users, records, sidebar

router = APIRouter()
router.include_router(users.router)
#router.include_router(groups.router)
router.include_router(records.router)
router.include_router(sidebar.router)
