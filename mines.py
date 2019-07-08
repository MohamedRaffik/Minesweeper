import curses
from enum import Enum
from random import seed, randint
from time import time
from sys import maxsize

class DISPLAY(Enum):
    UNCOVERED = 0
    COVERED = 1
    FLAGGED = 2

class Tile:
    Display = DISPLAY.COVERED
    ## -1 is MINE
    Number = 0

boards = [ 
    { 
        'name': 'Easy',
        'rows': 8,
        'cols': 8 ,
        'mines': 10
    },
    {
        'name': 'Medium',
        'rows': 16,
        'cols': 16,
        'mines': 40
    },
    {
        'name': 'Hard',
        'rows': 16,
        'cols': 30,
        'mines': 99
    }
]


def MainMenu(stdscr):
    title = 'Minesweeper'
    choices = [ f' {b["name"]} - {b["cols"]} x {b["rows"]} ' for b in boards ] + [ ' Exit ' ]
    options = '[^][v] - SELECT   [ENTER] - CONFIRM'
    pos = 0
    stdscr.clear()
    stdscr.addstr(1, curses.COLS // 2 - len(title) // 2, title, curses.A_BOLD)
    stdscr.addstr(curses.LINES * 2 // 3 + 3, curses.COLS // 2 - len(options) // 2, options, curses.A_NORMAL)
    while True:
        for i, c in enumerate(choices): 
            style = curses.A_STANDOUT if pos == i else curses.A_NORMAL
            stdscr.addstr(curses.LINES // 3 + i * 2, curses.COLS // 2 - len(c) // 2, c, style)
        key = stdscr.getch()
    
        if key == curses.KEY_UP and pos > 0:     
            pos -= 1
        elif key == curses.KEY_DOWN and pos < 3: 
            pos += 1
        elif key == ord('\n'):                   
            return pos



def GenerateDisplay(stdscr, board, board_attr, pos, mines, time_elapsed):
    title = 'Minesweeper'
    control = [ '[^][v][<][>] - ARROW KEYS TO MOVE   [SPACE] - UNCOVER   [1] - FLAG/UNCOVER SURROUNDING', '[^C] EXIT GAME' ]
    
    stdscr.addstr(1, curses.COLS // 2 - len(title) // 2, title, curses.A_BOLD)

    board_window = curses.newwin(board_attr['rows'] + 2, board_attr['cols'] * 2 + 3, 4, curses.COLS // 2 - ( board_attr['cols'] * 2 + 1 ) // 2)
    pos_y, pos_x = 0, 0
    
    for i, tile_row in enumerate(board):                    
        board_window.move(1 + i, 1)
        for j, tile_col in enumerate(tile_row):
            board_window.addstr(' ')
            pos_y, pos_x = board_window.getyx() if pos == ( i, j ) else ( pos_y, pos_x )

            if tile_col.Display == DISPLAY.COVERED:    
                board_window.addstr('#', curses.A_BOLD )
            elif tile_col.Display == DISPLAY.FLAGGED:  
                board_window.addstr('F', curses.A_BOLD | curses.color_pair(9))
            elif tile_col.Display == DISPLAY.UNCOVERED:
                if tile_col.Number > -1:  
                    board_window.addstr(f'{tile_col.Number if tile_col.Number != 0 else " "}', curses.A_BOLD | curses.color_pair(tile_col.Number)) 
                else:                     
                    board_window.addstr('M', curses.A_BOLD | curses.A_STANDOUT | curses.color_pair(10))
            
            if j % board_attr['cols'] == board_attr['cols'] - 1: board_window.addstr(' ')

    board_window.addstr(pos_y, pos_x - 1, '[')
    board_window.addstr(pos_y, pos_x + 1, ']')
    board_window.box()
    board_window.refresh()

    minutes = time_elapsed // 60
    seconds = time_elapsed % 60

    stdscr.move(3, 0)
    stdscr.clrtoeol()
    stdscr.addstr(3, curses.COLS // 4 - len('Mines: XX') // 2, f'Mines: {mines}')
    stdscr.addstr(3, curses.COLS // 2 - len('Time: XX:XX') // 2, f'Time: {minutes if minutes >= 10 else f"0{minutes}"}:{seconds if seconds >= 10 else f"0{seconds}"}')
    stdscr.addstr(3, curses.COLS * 3 // 4 - len('Flags: XX') // 2, f'Flags: {board_attr["mines"] - mines}')

    control_window = curses.newwin(4, curses.COLS, board_window.getmaxyx()[0] + 4, 0)
    
    for i, c in enumerate(control):
        control_window.addstr(i * 2 + 1, control_window.getmaxyx()[1] // 2 - len(c) // 2, c)
    
    control_window.refresh()




def GenerateMines(board, board_attr, pos):
    def IncrementTile(pos):
        pos_y, pos_x = pos
        if 0 <= pos_y < board_attr['rows'] and 0 <= pos_x < board_attr['cols']: 
            board[pos_y][pos_x].Number = board[pos_y][pos_x].Number + 1 if board[pos_y][pos_x].Number != -1 else -1

    seed()
    mine_pos = set()

    while len(mine_pos) < board_attr['mines']:
        mine_y, mine_x = randint(0, board_attr['rows'] - 1), randint(0, board_attr['cols'] - 1)
        
        if (mine_y, mine_x) != pos:
            mine_pos.add( (mine_y, mine_x) )

    for mine_y, mine_x in mine_pos:
        board[mine_y][mine_x].Number = -1
        IncrementTile( ( mine_y - 1, mine_x ) )
        IncrementTile( ( mine_y + 1, mine_x ) )
        IncrementTile( ( mine_y, mine_x - 1) )
        IncrementTile( ( mine_y, mine_x + 1) )
        IncrementTile( ( mine_y - 1, mine_x - 1) )
        IncrementTile( ( mine_y - 1, mine_x + 1) )
        IncrementTile( ( mine_y + 1, mine_x + 1) )
        IncrementTile( ( mine_y + 1, mine_x - 1) )



def UncoverTiles(board, board_attr, pos):
    def ClearSurrounding(pos, tiles):
        tile_y, tile_x = pos
        for neighbor_y in range( tile_y - 1, tile_y + 2):
            for neighbor_x in range( tile_x - 1, tile_x + 2):
                if 0 <= neighbor_y < board_attr['rows'] and 0 <= neighbor_x < board_attr['cols']:
                    if board[neighbor_y][neighbor_x].Display == DISPLAY.COVERED:
                        tiles.append( ( neighbor_y, neighbor_x ) )

    def CountFlags(pos):
        count = 0
        tile_y, tile_x = pos
        for neighbor_y in range( tile_y - 1, tile_y + 2):
            for neighbor_x in range( tile_x - 1, tile_x + 2):
                if 0 <= neighbor_y < board_attr['rows'] and 0 <= neighbor_x < board_attr['cols']:
                    count = count + 1 if board[neighbor_y][neighbor_x].Display == DISPLAY.FLAGGED else count
        return count

    tiles = [ pos ]

    if board[pos[0]][pos[1]].Display == DISPLAY.UNCOVERED:
        pos_y, pos_x = tiles.pop(0)
        if CountFlags(pos) == board[pos_y][pos_x].Number: 
            ClearSurrounding( ( pos_y, pos_x ), tiles )

    if board[pos[0]][pos[1]].Display != DISPLAY.FLAGGED:
        while len(tiles) > 0:
            pos_y, pos_x = tiles.pop(0)
            board[pos_y][pos_x].Display = DISPLAY.UNCOVERED
            
            if board[pos_y][pos_x].Number == 0: 
                ClearSurrounding( ( pos_y, pos_x ), tiles )



def CheckBoard(board):
    win = True
    for tile_row in board:
        for tile_col in tile_row:
            if tile_col.Display == DISPLAY.UNCOVERED and tile_col.Number == -1: 
                return -1
            elif ( tile_col.Display == DISPLAY.COVERED  or tile_col.Display == DISPLAY.FLAGGED) and tile_col.Number > -1:  
                win = False

    return 1 if win else 0



def MineSweeper(stdscr, best_time):

    choice = MainMenu(stdscr)

    if choice == 3: 
        exit()
    
    board = [ [ Tile() for j in range(boards[choice]['cols']) ] for i in range(boards[choice]['rows']) ]

    mines = boards[choice]['mines']
    first_move = True
    pos_y, pos_x = 0, 0
    stdscr.clear()
    start_time = int(time())
    current_time = start_time

    while True:

        GenerateDisplay(stdscr, board, boards[choice], (pos_y, pos_x), mines, current_time - start_time)
        status = CheckBoard(board)

        if status != 0:
            stdscr.move(3, 0)
            stdscr.clrtoeol()
            time_elapsed = current_time - start_time

            status_line = f'You {"Lost" if status == -1 else "WON !!"}'

            times = []

            if status == 1:
                for i, s in [ ( time_elapsed, 'Your Time' ), ( best_time[choice] if best_time[choice] < time_elapsed else time_elapsed, 'Best Time' ) ]:
                    minutes, seconds = i // 60, i % 60
                    times.append(f'{s}: {minutes if minutes > 10 else f"0{minutes}"}:{seconds if seconds > 10 else f"0{seconds}"}')

            line = '  '.join([ status_line, *times, 'Press Enter to Continue' ])

            
            stdscr.move(3, curses.COLS // 2 - len(line) // 2)
            stdscr.addstr(status_line, curses.A_BOLD)
            for t in times:
                stdscr.addstr(f'  {t}')
            stdscr.addstr('  [ Press Enter to Continue ]')

            while True:
                k = stdscr.getch()
                if k == ord('\n'): 
                    return time_elapsed if status == 1 else best_time[choice], choice

        key = stdscr.getch()
        
        if key == curses.KEY_DOWN:    
            pos_y = pos_y + 1 if pos_y < boards[choice]['rows'] - 1 else pos_y
        elif key == curses.KEY_UP:    
            pos_y = pos_y - 1 if pos_y > 0 else pos_y
        elif key == curses.KEY_RIGHT: 
            pos_x = pos_x + 1 if pos_x < boards[choice]['cols'] - 1 else pos_x
        elif key == curses.KEY_LEFT:  
            pos_x = pos_x - 1 if pos_x > 0 else pos_x
        elif key == ord('1'):
            if board[pos_y][pos_x].Display == DISPLAY.COVERED and mines > 0:   
                board[pos_y][pos_x].Display, mines = DISPLAY.FLAGGED, mines - 1
            elif board[pos_y][pos_x].Display == DISPLAY.FLAGGED and mines < boards[choice]['mines'] + 1: 
                board[pos_y][pos_x].Display, mines = DISPLAY.COVERED, mines + 1
            elif board[pos_y][pos_x].Display == DISPLAY.UNCOVERED:                                       
                UncoverTiles(board, boards[choice], ( pos_y, pos_x ) )
        
        elif key == ord(' '):

            if first_move:
                GenerateMines(board, boards[choice], ( pos_y, pos_x) )
                first_move = False

            UncoverTiles(board, boards[choice], ( pos_y, pos_x ) )

        elif key == ord('p'):

            time_paused = 0

            while True:
                unpause = stdscr.getch()
                time_paused = int(time()) - current_time

                if unpause == ord('p'):
                    start_time += time_paused
                    break

        current_time = int(time()) if not first_move else start_time



def Game(stdscr):
    curses.curs_set(0)
    curses.halfdelay(1)
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

    best_time = [ maxsize for i in range(len(boards)) ]

    while True:
        new_time, diff = MineSweeper(stdscr, best_time)
        best_time[diff] = new_time if new_time < best_time[diff] else best_time[diff]




if __name__ == "__main__":
    try:
        curses.wrapper(Game)
    except KeyboardInterrupt:
        exit()