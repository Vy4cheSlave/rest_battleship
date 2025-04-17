import random
from enum import Enum
from src.schemas import ShipPublic, GameBoardPublic, ShipType

BOARD_SIZE = 10

HORIZONTAL = 0

class HorizontalNameCell(Enum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7
    I = 8
    J = 9

    @classmethod
    def get_name(cls, value: int) -> str:
        try:
            return cls(value).name.lower()
        except ValueError:
            raise ValueError(f"The value {value} does not correspond to any element of the enumeration {cls.__name__}")

def generate_cell_id(row: int, col: int) -> str:
    return HorizontalNameCell.get_name(col) + str(row + 1)

SHIP_SIZES = [(ShipType.CRUISER, 4), 
    (ShipType.BATTLESHIP, 3), 
    (ShipType.BATTLESHIP, 3),
    (ShipType.DESTROYER, 2), 
    (ShipType.DESTROYER, 2),
    (ShipType.DESTROYER, 2),
    (ShipType.SPEEDBOAT, 1), 
    (ShipType.SPEEDBOAT, 1), 
    (ShipType.SPEEDBOAT, 1),
    (ShipType.SPEEDBOAT, 1),]

def generate_board() -> GameBoardPublic:
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    # ships_positions: set[string] = set()
    game_board = GameBoardPublic(ships=[])

    def can_place_ship(row, col, ship_size, orientation) -> bool:
        if orientation == HORIZONTAL: 
            if col + ship_size > BOARD_SIZE:
                return False
            for i in range(ship_size):
                if board[row][col + i] != 0:
                    return False
            # сверху
            if row > 0 and board[row - 1][col:col + ship_size] != [0] * ship_size:
                return False
            # снизу
            elif row < BOARD_SIZE - 1 and board[row + 1][col:col + ship_size] != [0] * ship_size:
                return False
            # слева
            elif col > 0 and board[row][col - 1] != 0:
                return False
            # справа
            elif col + ship_size < BOARD_SIZE and board[row][col + ship_size] != 0:
                return False
            # сверху слева
            elif col > 0 and row > 0 and board[row - 1][col - 1] != 0:
                return False
            # снизу слева
            elif col > 0 and row < BOARD_SIZE - 1 and board[row + 1][col - 1] != 0:
                return False
            # сверху справа
            elif col + ship_size < BOARD_SIZE and row > 0 and board[row - 1][col + ship_size] != 0:
                return False
            # снизу справа
            elif col + ship_size < BOARD_SIZE and row < BOARD_SIZE - 1 and board[row + 1][col + ship_size] != 0:
                return False

        else:
            if row + ship_size > BOARD_SIZE:
                return False
            for i in range(ship_size):
                if board[row + i][col] != 0:
                    return False
            # сверху
            if row > 0 and board[row - 1][col] != 0:
                return False
            # снизу
            elif row + ship_size < BOARD_SIZE and board[row + ship_size][col] != 0:
                return False
            # слева
            elif col > 0 and [board[row + i][col - 1] for i in range(ship_size)] != [0] * ship_size:
                return False
            # справа
            elif col < BOARD_SIZE - 1 and [board[row + i][col + 1] for i in range(ship_size)] != [0] * ship_size:
                return False
            # сверху слева
            elif row > 0 and col > 0 and row > 0 and board[row - 1][col - 1] != 0:
                return False
            # снизу слева
            elif row + ship_size < BOARD_SIZE and col > 0 and board[row + ship_size][col - 1] != 0:
                return False
            # сверху справа
            elif row > 0 and col < BOARD_SIZE - 1 and row > 0 and board[row - 1][col + 1] != 0:
                return False
            # снизу справа
            elif row + ship_size < BOARD_SIZE and col < BOARD_SIZE - 1 and row < BOARD_SIZE - 1 and board[row + ship_size][col + 1] != 0:
                return False

        return True

    for ship_size in SHIP_SIZES:
        placed = False
        while not placed:
            orientation = random.choice([0, 1])  # 0 - горизонтально, 1 - вертикально
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            
            if can_place_ship(row, col, ship_size[1], orientation):
                ship = ShipPublic(name=ship_size[0].value, location = [])

                if orientation == HORIZONTAL:
                    for i in range(ship_size[1]):
                        board[row][col + i] = 1
                        ship.location.append(generate_cell_id(row, col + i))
                else:
                    for i in range(ship_size[1]):
                        board[row + i][col] = 1
                        ship.location.append(generate_cell_id(row + i, col))

                placed = True
                game_board.ships.append(ship)

    return game_board