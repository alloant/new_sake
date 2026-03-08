from fastapi import APIRouter
from .auth import router as auth_router
from .main import router as main_router
from .fragments import router as fragments_router
from .api import router as api_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(main_router)
router.include_router(fragments_router)
router.include_router(api_router)
