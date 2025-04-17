from sqlmodel import SQLModel

class UserBase(SQLModel):
    username: str

class UserAuthPublic(UserBase):
    password: str

class UserPublic(UserBase):
    id: int
    disabled: bool