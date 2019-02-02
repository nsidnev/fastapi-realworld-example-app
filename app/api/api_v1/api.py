from fastapi import APIRouter

from .endpoints.article import router as article_router
from .endpoints.authenticaion import router as auth_router
from .endpoints.comment import router as comment_router
from .endpoints.profile import router as profile_router
from .endpoints.tag import router as tag_router
from .endpoints.user import router as user_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(profile_router)
router.include_router(comment_router)
router.include_router(article_router)
router.include_router(tag_router)
