from fastapi import APIRouter, status
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Home page"])


@router.get("/", status_code=status.HTTP_200_OK)
@cache(expire=120)
async def root():
    return {"Social Network Project": "This is the root of the project!"}
