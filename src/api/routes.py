from fastapi import APIRouter, Depends, HTTPException, Header, status
from typing import Annotated
from src.api.dependencies import SessionDep
from src.api.auth import check_access_token
from sqlmodel import select, exists, or_, and_
from sqlalchemy.orm import joinedload
from src.schemas import UserPublic, GameResult, GamePublic, GamePlayerPublic, GameBoardPublic
from src.models import User, Game, GameBoard, Ship
from src.game_board import generate_board

routes = APIRouter()

@routes.get("/players", response_model=list[UserPublic])
async def get_all_disabled_users(
    async_session: SessionDep,
    player: Annotated[User, Depends(check_access_token)],
    ):
    users_db = await async_session.execute(
        select(User).where(
            User.disabled==True,
            User.id != player.id,
        )
    )
    users_db = users_db.scalars().all()

    return users_db

@routes.post("/games/create", response_model=GamePlayerPublic)
async def create_game(
    async_session: SessionDep,
    player2_name: Annotated[str, Header()],
    player1: Annotated[User, Depends(check_access_token)],
    ):
    player2 = await async_session.execute(
        select(User).where(
            User.username==player2_name,
        )
    )
    player2 = player2.scalars().first()
    if not player2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with name \"{player2_name}\" not found.",
        )
    
    player1_board: GameBoardPublic = generate_board()
    player2_board: GameBoardPublic = generate_board()

    game_db: Game = Game(
        result=GameResult.NOT_STARTED.value,
        player1_name=player1.username,
        player2_name=player2.username,
        player1_id=player1.id,
        player2_id=player2.id
    )

    player1_board_db: GameBoard = GameBoard(ships=[])
    for ship in player1_board.ships:
        player1_board_db.ships.append(Ship(name=ship.name, location=ship.location))

    player2_board_db: GameBoard = GameBoard(ships=[])
    for ship in player2_board.ships:
        player2_board_db.ships.append(Ship(name=ship.name, location=ship.location))

    player1_board_db.player_id = player1.id
    player2_board_db.player_id = player2.id

    game_db.players_lived_board.extend([player1_board_db, player2_board_db])

    async_session.add(game_db)
    await async_session.commit()
    await async_session.refresh(game_db)

    game = GamePlayerPublic.parse_obj(game_db)

    for player_lived_board in game_db.players_lived_board:
        if player_lived_board.player_id == player1.id:
            game.player_lived_board = GameBoardPublic.parse_obj(player_lived_board)

    return game

@routes.get("/games", response_model=list[GamePlayerPublic])
async def get_not_ended_games(
    async_session: SessionDep,
    player: Annotated[User, Depends(check_access_token)],
    ):
    games_db = await async_session.execute(
        select(Game).where(
            or_(
                Game.player1_id == player.id,
                Game.player2_id == player.id
            ),
            or_(
                Game.result == GameResult.NOT_ENDED.value,
                Game.result == GameResult.NOT_STARTED.value,
            )
        ).options(joinedload(Game.players_lived_board))
    )
    games_db = games_db.unique().scalars().all()

    games: list[GamePlayerPublic] = []
    for game_db in games_db:
        game = GamePlayerPublic.parse_obj(game_db)
        for player_lived_board in game_db.players_lived_board:
            if player_lived_board.player_id == player.id:
                game.player_lived_board = GameBoardPublic.parse_obj(player_lived_board)
        games.append(game)

    return games

@routes.get("/players/{player_name}/stats", response_model=list[GamePublic])
async def get_game_stats_players(async_session: SessionDep, player_name: str):
    player = await async_session.execute(
        select(User).where(
            User.username==player_name,
        )
    )
    player = player.scalars().first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Player with name \"{player_name}\" not found.",
        )
    games_db = await async_session.execute(
        select(Game).where(
            or_(
                Game.player1_id == player.id,
                Game.player2_id == player.id
            ),
            and_(
                Game.result != GameResult.NOT_ENDED.value,
                Game.result != GameResult.NOT_STARTED.value
            )
        ).options(joinedload(Game.players_lived_board))
    )
    games_db = games_db.unique().scalars().all()

    return games_db