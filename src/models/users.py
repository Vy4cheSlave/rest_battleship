from src.schemas import UserAuthPublic
from sqlmodel import Field

class User(UserAuthPublic, table=True):
    id: int | None = Field(primary_key=True, default=None)
    disabled: bool = True