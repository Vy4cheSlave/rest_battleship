from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from src.schemas import ShipPublic, GameBoardBase
from typing import Optional

class Ship(ShipPublic, table=True):
    id: int | None = Field(primary_key=True, default=None)
    game_board_id: int | None = Field(foreign_key="gameboard.id")
    game_board: Optional["GameBoard"] = Relationship(back_populates="ships")

class GameBoard(GameBoardBase, table=True):
    id: int | None = Field(primary_key=True, default=None)
    game_sid: int | None = Field(foreign_key="game.sid", default=None)
    player_id: int | None = Field(foreign_key="user.id",  default=None)
    ships: list["Ship"] = Relationship(
        back_populates="game_board",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "joined"},
        )
    game: Optional["Game"] = Relationship(back_populates="players_lived_board")

    checked_cells: list[str] = Field(sa_column=Column(JSON), default_factory=list)

    def remove_ship(self, ship: Ship):
        self.ships.remove(ship)