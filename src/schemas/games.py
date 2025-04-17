from sqlmodel import SQLModel, Field
# from pydantic import BaseModel
from .ships import GameBoardPublic
from datetime import datetime
from enum import Enum

class GameResult(str, Enum):
    PLAYER_1_WIN = "player 1 win"
    PLAYER_2_WIN = "player 2 win"
    NOT_ENDED = "not ended"
    NOT_STARTED = "not started"

class GamePublic(SQLModel):
    sid: int
    end_date: datetime | None = None
    result: str
    player1_name: str
    player2_name: str

class GamePlayerPublic(GamePublic):
    player_lived_board: GameBoardPublic | None = None
    # players_lived_board: list[GameBoardPublic]