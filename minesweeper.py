import curses
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class DISPLAY(Enum):
    UNCOVERED = 0
    COVERED = 1
    FLAGGED = 2


@dataclass
class Tile:
    display: DISPLAY = DISPLAY.COVERED
    ## -1 is MINE
    number: int = 0


@dataclass
class Board:
    name: str
    rows: int
    cols: int
    mines: int
    grid: List[List[Tile]] = field(default_factory=lambda: list(list()))
    best_times = []

    def __str__(self):
        return f"{self.name} - {self.cols} x {self.rows}"

    def add_time(self, time: float = ...):
        self.best_times.append(time)
        self.best_times.sort()
        self.best_times = self.best_times[:5]


@dataclass
class Position:
    x: int = 0
    y: int = 0

    def __hash__(self):
        return hash((self.y, self.x))


class GameOverException(Exception):
    def __init__(self, win: bool = ...):
        self.win = win


class MineSweeper:
    def __init__(self, stdscr: curses.window = ...):
        self._stdscr = stdscr
        self._title = "Minesweeper"
        self._boards = [
            Board(name="Easy", rows=8, cols=8, mines=10),
            Board(name="Medium", rows=16, cols=16, mines=40),
            Board(name="Hard", rows=16, cols=30, mines=99),
        ]
        self.selected_board = self._boards[0]

    def exit_game(self):
        curses.nocbreak()
        curses.echo()
        raise KeyboardInterrupt()

    def main_menu(self):
        choices = [*[str(board) for board in self._boards], "Exit"]
        options = "[^][v] - SELECT   [ENTER] - CONFIRM"
        position = 0

        self._stdscr.clear()
        while True:
            self._stdscr.addstr(
                1,
                curses.COLS // 2 - len(self._title) // 2,
                self._title,
                curses.A_BOLD,
            )
            self._stdscr.addstr(
                curses.LINES * 2 // 3 + 3,
                curses.COLS // 2 - len(options) // 2,
                options,
                curses.A_NORMAL,
            )
            for i, choice in enumerate(choices):
                choice = f" {choice} "
                style = curses.A_STANDOUT if position == i else curses.A_NORMAL
                self._stdscr.addstr(
                    curses.LINES // 3 + i * 2,
                    curses.COLS // 2 - len(choice) // 2,
                    choice,
                    style,
                )
            key = self._stdscr.getch()
            if key == curses.KEY_UP and position > 0:
                position -= 1
            elif key == curses.KEY_DOWN and position < 3:
                position += 1
            elif key == ord("\n"):
                break
        if choices[position] == "Exit":
            raise self.exit_game()
        self.selected_board = self._boards[position]

    def _check_game_board(self):
        cleared = True
        for row in self.selected_board.grid:
            for tile in row:
                if tile.display == DISPLAY.UNCOVERED and tile.number == -1:
                    raise GameOverException(False)
                elif (
                    tile.display == DISPLAY.COVERED or tile.display == DISPLAY.FLAGGED
                ) and tile.number > -1:
                    cleared = False
        if cleared:
            raise GameOverException(True)
        return cleared

    def _format_seconds(self, seconds: float = ...):
        seconds = int(seconds)
        return "Time: {minutes}:{seconds}".format(
            minutes=str(seconds // 60).rjust(2, "0"),
            seconds=str(seconds % 60).rjust(2, "0"),
        )

    def _render_game_display(
        self,
        mines: int = ...,
        current_position: Position = ...,
        start_time: float = ...,
    ):
        self._stdscr.addstr(
            1, curses.COLS // 2 - len(self._title) // 2, self._title, curses.A_BOLD
        )
        board_window = curses.newwin(
            self.selected_board.rows + 2,
            self.selected_board.cols * 2 + 3,
            4,
            curses.COLS // 2 - (self.selected_board.cols * 2 + 1) // 2,
        )
        for y, row in enumerate(self.selected_board.grid):
            board_window.move(y + 1, 1)
            for tile in row:
                board_window.addstr(" ")
                if tile.display == DISPLAY.COVERED:
                    board_window.addstr("#", curses.A_BOLD)
                elif tile.display == DISPLAY.FLAGGED:
                    board_window.addstr("F", curses.A_BOLD | curses.color_pair(9))
                elif tile.display == DISPLAY.UNCOVERED:
                    if tile.number > -1:
                        board_window.addstr(
                            f'{tile.number if tile.number != 0 else " "}',
                            curses.A_BOLD | curses.color_pair(tile.number),
                        )
                    else:
                        board_window.addstr(
                            "M",
                            curses.A_BOLD | curses.A_STANDOUT | curses.color_pair(10),
                        )
            board_window.addstr(" ")
        board_window_position = Position(
            x=(current_position.x + 1) * 2, y=current_position.y + 1
        )
        board_window.addstr(board_window_position.y, board_window_position.x - 1, "[")
        board_window.addstr(board_window_position.y, board_window_position.x + 1, "]")
        board_window.box()
        board_window.refresh()
        self._stdscr.move(3, 0)
        self._stdscr.clrtoeol()
        self._stdscr.addstr(
            3, curses.COLS // 4 - len("Mines: XX") // 2, f"Mines: {mines}"
        )
        time_elapsed = int(time.time() - start_time)
        self._stdscr.addstr(
            2,
            curses.COLS // 2 - len("Time: XX:XX") // 2,
            self._format_seconds(seconds=time_elapsed),
        )
        controls = [
            "[^][v][<][>] - ARROW KEYS TO MOVE   [SPACE] - UNCOVER   [1] - FLAG/UNCOVER SURROUNDING",
            "[^C] EXIT GAME",
        ]
        board_window_max_y, _ = board_window.getmaxyx()
        control_window = curses.newwin(2, curses.COLS, board_window_max_y + 4, 0)
        for i, control in enumerate(controls):
            _, control_window_max_x = control_window.getmaxyx()
            control_window.addstr(
                0 + i,
                control_window_max_x // 2 - len(control) // 2,
                control,
            )
        control_window.refresh()

    def _get_surrounding_positions(self, position: Position = ...):
        positions: List[Position] = []
        for y in range(position.y - 1, position.y + 2):
            for x in range(position.x - 1, position.x + 2):
                surrounding_position = Position(x=x, y=y)
                if surrounding_position == position:
                    continue
                tile = self._get_tile_from_position(position=surrounding_position)
                if tile:
                    positions.append(surrounding_position)
        return positions

    def _generate_mines(self, current_position: Position = ...):
        random.seed()
        created_mines = 0
        while created_mines < self.selected_board.mines:
            mine_position = Position(
                x=random.randint(0, self.selected_board.cols - 1),
                y=random.randint(0, self.selected_board.rows - 1),
            )
            mine_tile = self._get_tile_from_position(position=mine_position)
            if mine_position != current_position and mine_tile.number != -1:
                mine_tile.number = -1
                for surrounding_position in self._get_surrounding_positions(
                    position=mine_position
                ):
                    tile = self._get_tile_from_position(position=surrounding_position)
                    if tile:
                        tile.number = tile.number + 1 if tile.number != -1 else -1
                created_mines += 1

    def _get_tile_from_position(self, position: Position = ...):
        if (
            0 <= position.y < self.selected_board.rows
            and 0 <= position.x < self.selected_board.cols
        ):
            return self.selected_board.grid[position.y][position.x]
        return None

    def _uncover_tiles(self, current_position: Position = ...):
        positions = [current_position]
        current_tile = self._get_tile_from_position(position=current_position)
        if not current_tile:
            return
        if current_tile.display == DISPLAY.UNCOVERED:
            surrounding_positions = self._get_surrounding_positions(
                position=current_position
            )
            flags = 0
            for surrounding_position in surrounding_positions:
                surrounding_tile = self._get_tile_from_position(
                    position=surrounding_position
                )
                if surrounding_tile and surrounding_tile.display == DISPLAY.FLAGGED:
                    flags += 1
            if current_tile.number <= flags:
                positions = surrounding_positions
        while positions:
            tile_position = positions.pop()
            tile = self._get_tile_from_position(position=tile_position)
            if tile and tile.display == DISPLAY.COVERED:
                tile.display = DISPLAY.UNCOVERED
                if tile.number == 0:
                    for surrounding_position in self._get_surrounding_positions(
                        position=tile_position
                    ):
                        positions.append(surrounding_position)

    def run_game(self):
        mines = self.selected_board.mines
        self.selected_board.grid = [
            [
                Tile(display=DISPLAY.COVERED, number=0)
                for _ in range(self.selected_board.cols)
            ]
            for _ in range(self.selected_board.rows)
        ]
        position = Position()
        start_time = time.time()
        first_move = True

        self._stdscr.clear()
        while True:
            self._render_game_display(
                mines=mines, current_position=position, start_time=start_time
            )
            try:
                self._check_game_board()
            except GameOverException as e:
                self._stdscr.move(3, 0)
                self._stdscr.clrtoeol()
                status_line = f'You {"WON" if e.win else "LOST"} !!'
                if e.win:
                    time_elapsed = time.time() - start_time
                    self.selected_board.add_time(time=time_elapsed)

                times = [
                    f"{i + 1}. {self._format_seconds(seconds=best_time)}"
                    for i, best_time in enumerate(self.selected_board.best_times)
                ]

                line = "  ".join([status_line, *times, "[ Press Enter to Continue ]"])

                self._stdscr.move(3, curses.COLS // 2 - len(line) // 2)
                self._stdscr.addstr(line, curses.A_BOLD)

                while True:
                    key = stdscr.getch()
                    if key == ord("\n"):
                        break
                break

            key = stdscr.getch()
            if key == curses.KEY_DOWN:
                position.y = min(position.y + 1, self.selected_board.rows - 1)
            elif key == curses.KEY_UP:
                position.y = max(position.y - 1, 0)
            elif key == curses.KEY_RIGHT:
                position.x = min(position.x + 1, self.selected_board.cols - 1)
            elif key == curses.KEY_LEFT:
                position.x = max(position.x - 1, 0)
            elif key == ord("1"):
                tile = self._get_tile_from_position(position=position)
                if not tile:
                    continue
                elif tile.display == DISPLAY.COVERED and mines > 0:
                    tile.display = DISPLAY.FLAGGED
                    mines -= 1
                elif (
                    tile.display == DISPLAY.FLAGGED
                    and mines < self.selected_board.mines
                ):
                    tile.display = DISPLAY.COVERED
                    mines += 1
                elif tile.display == DISPLAY.UNCOVERED:
                    self._uncover_tiles(current_position=position)
            elif key == ord(" "):
                if first_move:
                    self._generate_mines(current_position=position)
                    first_move = False
                tile = self._get_tile_from_position(position=position)
                self._uncover_tiles(current_position=position)

    def loop(self):
        self._stdscr.keypad(True)
        while True:
            self.main_menu()
            self.run_game()


if __name__ == "__main__":
    stdscr = curses.initscr()
    curses.curs_set(0)
    curses.cbreak()
    curses.halfdelay(1)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(0, curses.COLOR_BLACK, curses.COLOR_BLACK)
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(9, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(10, curses.COLOR_RED, curses.COLOR_BLACK)

    try:
        game = MineSweeper(stdscr=stdscr)
        game.loop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        raise e
    finally:
        curses.endwin()
