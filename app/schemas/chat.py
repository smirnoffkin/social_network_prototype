from pydantic import BaseModel


class ShowMessage(BaseModel):
    id: int
    message: str

    class Config:
        orm_mode = True
