from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Depends, WebSocketException
from src.api.auth import check_access_token_websocket
from src.models import User, Game, GameBoard, Ship
from src.api.dependencies import SessionDep
from src.schemas import ServerMessage, ClientMessage, GameResult
from sqlmodel import select, or_, and_
from typing import Annotated
import random
from pydantic import ValidationError
import json
from datetime import datetime

websoket_router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, player_id: int, websocket: WebSocket) -> bool:
        if player_id in self.active_connections:
            return False
        else:
            await websocket.accept()
            self.active_connections[player_id] = websocket
            return True

    def disconnect(self, player_id: int) -> bool:
        try:
            del self.active_connections[player_id]
            return True
        except KeyError:
            return False

    def get_websocket_by_id(self, player_id: int) -> WebSocket | None:
        if player_id in self.active_connections:
            return self.active_connections[player_id]
        else:
            return None

    def check_player(self, player_id: int) -> bool:
        if player_id in self.active_connections:
            return True
        else:
            return False
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(
            ServerMessage(message=message).dict()
            )

    async def send_player_message(self, message: str, player_id: int):
        if player_id in self.active_connections:
            await self.send_personal_message(
                message=message, 
                websocket=self.active_connections[player_id], 
                )

    async def send_message_play_room(self, message: str, first_player_websocket: WebSocket, second_player_id: int):
        await self.send_personal_message(message, first_player_websocket)
        await self.send_player_message(
            message=message,
            player_id=second_player_id,
            )

    async def receive_message(self, websocket: WebSocket) -> ClientMessage | None:
        try:
            data = await websocket.receive_json()
            client_message = ClientMessage.parse_obj(data)
            return client_message
        except (json.JSONDecodeError, ValidationError):
            return None

class GamesManager:
    def __init__(self):
        self.active_games: dict[int, Game] = {}

    def add_game(self, game:Game):
        if game.sid not in self.active_games:
            self.active_games[game.sid] = game
        if self.active_games[game.sid].next_step_player_name is None:
            next_step = random.randint(0, 1)
            if next_step == 0:
                self.active_games[game.sid].next_step_player_name = game.player1_name
            else:
                self.active_games[game.sid].next_step_player_name = game.player2_name

    def get_game(self, game_sid: int) -> Game | None:
        if game_sid in self.active_games:
            return self.active_games[game_sid]
        else: 
            return None

    def delete_game(self, game_sid: int):
        try:
            del self.active_games[game_sid]
        except KeyError:
            return

    def set_next_step_player(self, game_sid: int, player_name: str):
        self.active_games[game_sid].next_step_player_name = player_name

    def get_next_step_player(self, game_sid: int, player_name: str) -> str:
        return self.active_games[game_sid].next_step_player_name

    def set_result(self, game_sid, result_if_player_win: int):
        game = self.get_game(game_sid)
        game.end_date = datetime.now()
        if result_if_player_win == 0:
            game.result = GameResult.PLAYER_1_WIN.value
        else:
            game.result = GameResult.PLAYER_2_WIN.value


manager = ConnectionManager()
active_games = GamesManager()

@websoket_router.websocket("/games/{game_sid}/play")
async def play_room(
    *,
    websocket: WebSocket, 
    async_session: SessionDep,
    player: Annotated[User, Depends(check_access_token_websocket)],
    game_sid: int,
    ):
    game_db: Game = await async_session.execute(
        select(Game).where(
            Game.sid == game_sid,
            and_(
                Game.result != GameResult.PLAYER_1_WIN.value,
                Game.result != GameResult.PLAYER_2_WIN.value,
            )
        )
    )
    game_db = game_db.scalars().first()

    if not game_db:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Game not found or already ended",
        )
    if player.id != game_db.player1_id and player.id != game_db.player2_id:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="You do not have access to this game",
        )

    if not await manager.connect(player.id, websocket):
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="You already accessed to game",
        )
    player.disabled = False
    await async_session.merge(player)
    await async_session.commit()

    active_games.add_game(game_db)

    if player.id == game_db.player1_id:
        player2_id = game_db.player2_id
        player2_name = game_db.player2_name
        result_if_player_win = 0
    else:
        player2_id = game_db.player1_id
        player2_name = game_db.player1_name
        result_if_player_win = 1

    await manager.send_message_play_room(
        message=f"Player \"{player.username}\" is connected",
        first_player_websocket=websocket,
        second_player_id=player2_id
        )

    game = active_games.get_game(game_sid)

    player2_lived_board_index: int
    for board_index, board in enumerate(game.players_lived_board):
        if board.player_id == player2_id:
            player2_lived_board_index = board_index

    if manager.check_player(player2_id):
        if game.result == GameResult.NOT_STARTED.value:
            await manager.send_message_play_room(
                message=f"Start Game. Next step is \"{game.next_step_player_name}\"",
                first_player_websocket=websocket,
                second_player_id=player2_id
                )
            game.result = GameResult.NOT_ENDED.value
        else:
            await manager.send_message_play_room(
                message=f"Game Continued. Next step is \"{game.next_step_player_name}\"",
                first_player_websocket=websocket,
                second_player_id=player2_id
                )

    # game process
    try:
        while True:
            data = await manager.receive_message(websocket)
            if data is not None:
                if manager.check_player(player2_id):
                    if game.next_step_player_name == player.username:
                        cell = data.x.lower() + str(data.y)
                        # сделать проверку на то дублирующийся ли это ход
                        await manager.send_message_play_room(
                            message=f"{player.username} has made a move on \"{cell}\"", 
                            first_player_websocket=websocket,
                            second_player_id=player2_id,
                            )
                        is_not_hitted = True
                        for ship_index, ship in enumerate(game.players_lived_board[player2_lived_board_index].ships[:]):
                            if cell in ship.location:
                                is_not_hitted = False
                                if len(ship.location) == 1:
                                    game.players_lived_board[player2_lived_board_index].remove_ship(ship)
                                    await manager.send_message_play_room(
                                        message=f"{player.username} kill ship. Next step is {player.username}.", 
                                        first_player_websocket=websocket,
                                        second_player_id=player2_id,
                                        )
                                    if len(game.players_lived_board[player2_lived_board_index].ships) == 0:
                                        await manager.send_message_play_room(
                                            message=f"{player.username} win.", 
                                            first_player_websocket=websocket,
                                            second_player_id=player2_id,
                                            )
                                        active_games.set_result(game_sid, result_if_player_win)
                                        
                                        game.players_lived_board = []
                                        player2_websocket = manager.get_websocket_by_id(player2_id)
                                        if player2_websocket is not None:
                                            await player2_websocket.close(code=1000, reason=None)
                                        await websocket.close(code=1000, reason=None)
                                else:
                                    game.players_lived_board[player2_lived_board_index].ships[ship_index].remove_location(cell)
                                    await manager.send_message_play_room(
                                        message=f"{player.username} hit ship. Next step is {player.username}.", 
                                        first_player_websocket=websocket,
                                        second_player_id=player2_id,
                                        )
                                break
                        if is_not_hitted:
                            await manager.send_message_play_room(
                                message=f"{player.username} miss. Next step is {player2_name}.", 
                                first_player_websocket=websocket,
                                second_player_id=player2_id,
                                )
                            game.next_step_player_name = player2_name
                            
                    else:
                        await manager.send_personal_message(
                            message=f"It's \"{game.next_step_player_name}\" turn to walk now", 
                            websocket=websocket
                            )
                else:
                    await manager.send_personal_message(
                        message=f"Game Paused. Second player is disconnected", 
                        websocket=websocket,
                        )
            else:
                await manager.send_personal_message(
                    message=f"ERROR: The data is not JSON or cannot be validated", 
                    websocket=websocket,
                    )

    except WebSocketDisconnect:
        player.disabled = True
        await async_session.merge(player)

        if not manager.check_player(player2_id):
            game = active_games.get_game(game_sid)
            if game is not None:
                await async_session.merge(game)
            active_games.delete_game(game_sid)

        await async_session.commit()
        manager.disconnect(player.id)
        await manager.send_player_message(
            message=f"Player \"{player.username}\" is disconnected",
            player_id=player2_id,
            )