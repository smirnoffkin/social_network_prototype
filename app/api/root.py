from fastapi import APIRouter, status

router = APIRouter(tags=["Home page"])


@router.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"Social Network Project": "This is the root of the project!"}
