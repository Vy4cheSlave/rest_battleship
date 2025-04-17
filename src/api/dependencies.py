from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]