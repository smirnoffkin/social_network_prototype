from fastapi import APIRouter

from . import admin, auth, chat, follow, root, post, test, user

main_api_router = APIRouter()

main_api_router.include_router(admin.router)
main_api_router.include_router(auth.router)
main_api_router.include_router(chat.router)
main_api_router.include_router(follow.router)
main_api_router.include_router(root.router)
main_api_router.include_router(post.router)
main_api_router.include_router(test.router)
main_api_router.include_router(user.router)
