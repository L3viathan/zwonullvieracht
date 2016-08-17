import os
import sys
import termios
import tty
import subprocess
from typing import Tuple, List
from random import randint, random


"""
This dictionary defines the chances of tile appearance.
Keys are the tile values, values are the "weights".
1: 3, 4: 1 means 1 comes 75% of the time.
"""

loot_table = {
        1: 3,
        4: 1,
            }

def clear_screen() -> None:
    """Clears the screen"""
    if os.name == "posix":
        subprocess.run("clear")
    else:  # probably Windows
        subprocess.run("clr")


def print_board(board: List[List[int]]) -> None:
    """Print the 2048 board."""
    clear_screen()
    print("-"*(4*4 + 5))
    for row in range(4):
        print("|", end='')
        for col in range(4):
            number = board[row][col]
            if number == 0: number = ''
            print(str(number).center(4), end='|')
        print("")
        print("-"*(4*4 + 5))


def stringify(board: List[List[int]]) -> str:
    """Return a stringified version of the board, for identity checking."""
    return ''.join(''.join(str(board[row][col]) for col in range(4)) for row in range(4))


def move(board: List[List[int]], direction: str) -> Tuple[int, bool]:
    """
    (Try to) move in the given direction.
    
    Return the points, and whether change happened.
    """
    sign, r = (1, range(3, -1, -1)) if direction in ('right', 'down') else (-1, range(4))
    vertical = direction in ('up', 'down')

    points = 0
    pre = stringify(board)

    if vertical:
        for col in range(4):
            for row in r:
                while True:
                    if row >= 3 and direction == "down" or row <= 0 and direction == "up":
                        break
                    if board[row+sign][col] == 0:
                        board[row+sign][col] = board[row][col]
                        board[row][col] = 0
                        row += sign
                    elif abs(board[row][col]) == abs(board[row+sign][col]):
                        board[row+sign][col] += board[row][col]
                        board[row][col] = 0
                        row += sign
                        points += board[row][col]
                    else:
                        break
    else:
        for row in range(4):
            for col in r:
                while True:
                    if col >= 3 and direction == "right" or col <= 0 and direction == "left":
                        break
                    if board[row][col+sign] == 0:
                        board[row][col+sign] = board[row][col]
                        board[row][col] = 0
                        col += sign
                    elif abs(board[row][col]) == abs(board[row][col+sign]):
                        board[row][col+sign] += board[row][col]
                        board[row][col] = 0
                        col += sign
                        points += board[row][col]
                    else:
                        break

    post = stringify(board)
    return points, pre != post


def is_full(board: List[List[int]]) -> bool:
    """Return True iff the board is full (no empty cells)."""
    return all(all(board[row][col] != 0 for row in range(4)) for col in range(4))


def is_game_over(board: List[List[int]]) -> bool:
    """Return True iff no more moves are possible."""
    if not is_full(board):
        return False
    if any(any(board[row][col] == board[row][col+1] for col in range(3)) for row in range(4)):
        return False
    if any(any(board[row][col] == board[row+1][col] for row in range(3)) for col in range(4)):
        return False
    return True


def get_direction() -> str:
    """
    Await a keypress and return a direction.

    Supported  keys are the arrow keys, WASD, and hjkl. If ^C is pressed,
    raise a KeyboardInterrupt as expected.
    """
    mappings = {
            'A': 'up',
            'B': 'down',
            'C': 'right',
            'D': 'left',
            'a': 'left',
            'd': 'right',
            's': 'down',
            'w': 'up',
            'h': 'left',
            'j': 'down',
            'k': 'up',
            'l': 'right',
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
        if ch != '\x1b':  # not an escape sequence
            continue
        ch = sys.stdin.read(1)
        if ord(ch) == 3:  # ^C
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            raise KeyboardInterrupt
        if ch != '[':  # not an escape sequence (of the right type)
            continue
        ch = sys.stdin.read(1)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if ord(ch) == 3:  # ^C
            raise KeyboardInterrupt
        if ch not in "ABCD":
            continue
        return mappings[ch]


def add_random_tile(board: List[List[int]]) -> None:
    """(Try to) add a random tile on the board, and return the new board."""
    if is_full(board):
        return board
    def get_tile():
        N = sum(loot_table.values())
        rand = random()
        for choice, weight in loot_table.items():
            if rand < weight/N:
                return choice
            else:
                rand -= weight/N
        return 'E'
    while True:
        row, col = randint(0,3), randint(0,3)
        if board[row][col] != 0:
            continue
        board[row][col] = get_tile()
        return


board = [
        [0,0,0,0],
        [0,0,0,0],
        [0,0,0,0],
        [0,0,0,0],
        ]

score = 0

add_random_tile(board)
add_random_tile(board)
print_board(board)

last = stringify(board)

while True:
    direction = get_direction()
    points, change = move(board, direction)
    now = stringify(board)
    score += points
    if change: add_random_tile(board)
    if now != last:
        print_board(board)
        print(score)
        last = now
    if is_game_over(board):
        print("GAME OVER")
        break
