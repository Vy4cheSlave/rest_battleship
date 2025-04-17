from sqlmodel import SQLModel, Field, Relationship
from src.schemas import GamePublic
from typing import Optional

class Game(GamePublic, table=True):
    sid: int | None = Field(primary_key=True, default=None)
    player1_id: int | None = Field(foreign_key="user.id")
    player2_id: int | None = Field(foreign_key="user.id")
    next_step_player_name: str | None = None

    players_lived_board: list["GameBoard"] = Relationship(
        back_populates="game",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "joined"},
        )