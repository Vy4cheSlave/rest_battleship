from pydantic import BaseModel
from pydantic import BaseModel, Field

class ServerMessage(BaseModel):
    message: str

class ClientMessage(BaseModel):
    x: str = Field(pattern='^[a-jA-J]$')
    y: int = Field(ge=1, le=10)