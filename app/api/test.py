from fastapi import APIRouter, status

router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    return {"Ping": "Pong!"}
