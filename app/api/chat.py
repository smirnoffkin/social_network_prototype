from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.connection import get_db, async_session
from app.db.postgres.models import Message
from app.schemas.chat import ShowMessage

router = APIRouter(prefix="/chat", tags=["Chat"])

templates = Jinja2Templates(directory="./app/templates")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, add_to_db: bool):
        if add_to_db:
            await self.add_messages_to_database(message)
        for connection in self.active_connections:
            await connection.send_text(message)

    @staticmethod
    async def add_messages_to_database(message: str):
        session: AsyncSession = async_session()
        async with session.begin():
            stmt = insert(Message).values(message=message)
            await session.execute(stmt)
            await session.commit()


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(
                message=f"Client #{client_id} says: {data}",
                add_to_db=True
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(
            message=f"Client #{client_id} left the chat",
            add_to_db=False
        )


@router.get("/last_messages", response_model=list[ShowMessage])
async def get_last_messages(db: AsyncSession = Depends(get_db)):
    query = select(Message).order_by(Message.id.desc()).limit(5)
    messages = await db.execute(query)
    return messages.scalars().all()


@router.get("/public_chat", response_class=HTMLResponse)
async def get_public_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
