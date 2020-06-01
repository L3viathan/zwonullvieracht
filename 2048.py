"""
2048 implementation in Python/termios
"""
import os
import ast
import sys
import termios
import tty
import subprocess
from typing import Tuple, List, Dict, Union
from random import randint, random


"""
This dictionary defines the chances of tile appearance.
Keys are the tile values, values are the "weights".
1: 3, 4: 1 means 1 comes 75% of the time.
"""


def clear_screen() -> None:
    """Clears the screen"""
    if os.name == "posix":
        subprocess.run("clear")
    else:  # probably Windows
        subprocess.run("clr")


def print_board(board: List[List[int]]) -> None:
    """Print the 2048 board."""
    clear_screen()
    print("-" * (4 * Y + 5))
    for row in range(X):
        print("|", end="")
        for col in range(Y):
            number = board[row][col]
            if number == 0:
                number = ""
            print(str(number).center(4), end="|")
        print("")
        print("-" * (4 * Y + 5))


def stringify(board: List[List[int]]) -> str:
    """Return a stringified version of the board, for identity checking."""
    return "".join(
        "".join(str(board[row][col]) for col in range(Y)) for row in range(X)
    )


def move(board: List[List[int]], direction: str) -> Tuple[int, bool]:
    """
    (Try to) move in the given direction.

    Return the points, and whether change happened.
    """
    if direction == "right":
        sign = 1
        r = range(Y - 1, -1, -1)
    elif direction == "down":
        sign = 1
        r = range(X - 1, -1, -1)
    elif direction == "left":
        sign = -1
        r = range(Y)
    elif direction == "up":
        sign = -1
        r = range(X)

    vertical = direction in ("up", "down")

    points = 0
    pre = stringify(board)

    if vertical:
        for col in range(Y):
            for row in r:
                while True:
                    if (
                        row >= X - 1
                        and direction == "down"
                        or row <= 0
                        and direction == "up"
                    ):
                        break
                    if board[row + sign][col] == 0:
                        board[row + sign][col] = board[row][col]
                        board[row][col] = 0
                        row += sign
                    elif abs(board[row][col]) == abs(board[row + sign][col]):
                        board[row + sign][col] += board[row][col]
                        board[row][col] = 0
                        row += sign
                        points += board[row][col]
                    else:
                        break
    else:
        for row in range(X):
            for col in r:
                while True:
                    if (
                        col >= Y - 1
                        and direction == "right"
                        or col <= 0
                        and direction == "left"
                    ):
                        break
                    if board[row][col + sign] == 0:
                        board[row][col + sign] = board[row][col]
                        board[row][col] = 0
                        col += sign
                    elif abs(board[row][col]) == abs(board[row][col + sign]):
                        board[row][col + sign] += board[row][col]
                        board[row][col] = 0
                        col += sign
                        points += board[row][col]
                    else:
                        break

    post = stringify(board)
    return points, pre != post


def is_full(board: List[List[int]]) -> bool:
    """Return True iff the board is full (no empty cells)."""
    return all(all(board[row][col] != 0 for row in range(X)) for col in range(Y))


def is_game_over(board: List[List[int]]) -> bool:
    """Return True iff no more moves are possible."""
    if not is_full(board):
        return False
    if any(
        any(board[row][col] == board[row][col + 1] for col in range(Y - 1))
        for row in range(X)
    ):
        return False
    if any(
        any(board[row][col] == board[row + 1][col] for row in range(X - 1))
        for col in range(Y)
    ):
        return False
    return True


def get_direction() -> str:
    """
    Await a keypress and return a direction.

    Supported  keys are the arrow keys, WASD, and hjkl. If ^C is pressed,
    raise a KeyboardInterrupt as expected.
    """
    mappings = {
        "A": "up",
        "B": "down",
        "C": "right",
        "D": "left",
        "a": "left",
        "d": "right",
        "s": "down",
        "w": "up",
        "h": "left",
        "j": "down",
        "k": "up",
        "l": "right",
    }
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(sys.stdin.fileno())
    while True:  # loop until we have a direction
        ch = sys.stdin.read(1)
        if ord(ch) == 3:  # ^C
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            raise KeyboardInterrupt
        if ch in "wasdhjkl":
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            return mappings[ch]
        if ch != "\x1b":  # not an escape sequence
            continue
        ch = sys.stdin.read(1)
        if ord(ch) == 3:  # ^C
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            raise KeyboardInterrupt
        if ch != "[":  # not an escape sequence (of the right type)
            continue
        ch = sys.stdin.read(1)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if ord(ch) == 3:  # ^C
            raise KeyboardInterrupt
        if ch not in "ABCD":
            continue
        return mappings[ch]


def add_random_tile(
    board: List[List[int]], settings: Dict[int, Union[int, float]],
) -> None:
    """(Try to) add a random tile on the board, and return the new board."""
    if is_full(board):
        return board

    def get_tile():
        N = sum(settings.values())
        rand = random()
        for choice, weight in settings.items():
            if rand < weight / N:
                return choice
            else:
                rand -= weight / N
        return "E"

    while True:
        row, col = randint(0, X - 1), randint(0, Y - 1)
        if board[row][col] != 0:
            continue
        board[row][col] = get_tile()
        return


if __name__ == "__main__":
    subprocess.run(["tput", "smcup"])
    if len(sys.argv) > 1:
        SETTINGS = ast.literal_eval(sys.argv[1])
    else:
        SETTINGS = {
            1: 3,
            4: 1,
        }
    if len(sys.argv) > 2:
        X, Y = map(int, sys.argv[2].split("x"))
    else:
        X, Y = 4, 4

    BOARD = []
    for _ in range(X):
        BOARD.append([0] * Y)

    score = 0

    add_random_tile(BOARD, SETTINGS)
    add_random_tile(BOARD, SETTINGS)
    print_board(BOARD)

    last = stringify(BOARD)

    while True:
        direction = get_direction()
        POINTS, change = move(BOARD, direction)
        now = stringify(BOARD)
        score += POINTS
        if change:
            add_random_tile(BOARD, SETTINGS)
        if now != last:
            print_board(BOARD)
            print(score)
            last = now
        if is_game_over(BOARD):
            print("GAME OVER")
            break
    subprocess.run(["tput", "rmcup"])
