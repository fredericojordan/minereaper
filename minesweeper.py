import random
import sys

import pygame
from pygame.locals import *

# AI
AI_ENABLED = True

# GAME
FIELDWIDTH = 9
FIELDHEIGHT = 9
MINESTOTAL = 10

# UI
FPS = 30
WINDOWWIDTH = 400
WINDOWHEIGHT = 490
BOXSIZE = 30
GAPSIZE = 5
XMARGIN = int((WINDOWWIDTH-(FIELDWIDTH*(BOXSIZE+GAPSIZE)))/2)
YMARGIN = XMARGIN

# INPUT
LEFT_CLICK = 1
RIGHT_CLICK = 3

# assertions
assert MINESTOTAL < FIELDHEIGHT*FIELDWIDTH, 'More mines than boxes'
assert BOXSIZE^2 * (FIELDHEIGHT*FIELDWIDTH) < WINDOWHEIGHT*WINDOWWIDTH, 'Boxes will not fit on screen'
assert BOXSIZE/2 > 5, 'Bounding errors when drawing rectangle, cannot use half-5 in draw_mines_numbers'

# COLORS
LIGHTGRAY = (225, 225, 225)
DARKGRAY = (160, 160, 160)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 128, 0)

# set up major colors
BGCOLOR = WHITE
FIELDCOLOR = BLACK
BOXCOLOR_COV = DARKGRAY # covered box color
BOXCOLOR_REV = LIGHTGRAY # revealed box color
MINECOLOR = BLACK
TEXTCOLOR_1 = BLUE
TEXTCOLOR_2 = RED
TEXTCOLOR_3 = BLACK
HILITECOLOR = GREEN
RESETBGCOLOR = LIGHTGRAY
MINEMARK_COV = RED

# set up font 
FONTTYPE = 'Courier New'
FONTSIZE = 20

MINE = 'X'

class Minesweeper():
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Minesweeper')
        
        # initialize global variables & pygame module, set caption
        global BASICFONT, RESET_SURF, RESET_RECT, SHOW_SURF, SHOW_RECT
        
        self.clock = pygame.time.Clock()
        self._display_surface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        BASICFONT = pygame.font.SysFont(FONTTYPE, FONTSIZE)
    
        # obtain reset & show objects and rects
        RESET_SURF, RESET_RECT = draw_button('RESET', TEXTCOLOR_3, RESETBGCOLOR, WINDOWWIDTH/2, WINDOWHEIGHT-75)
        SHOW_SURF, SHOW_RECT = draw_button('SHOW ALL', TEXTCOLOR_3, RESETBGCOLOR, WINDOWWIDTH/2, WINDOWHEIGHT-50)
        
        # set background color
        self._display_surface.fill(BGCOLOR)
        
        self.database = []
        self.new_game()
        
    def new_game(self):
        """Set up mine field data structure, list of all zeros for recursion, and revealed box boolean data structure"""
        self.mine_field = get_random_minefield()
        self.revealed_boxes = blank_revealed_box_data(False)
        self.marked_mines = []
        
    def draw_field(self):
        """Draws field GUI"""
        
        self._display_surface.fill(BGCOLOR)
        pygame.draw.rect(self._display_surface, FIELDCOLOR, (XMARGIN-5, YMARGIN-5, (BOXSIZE+GAPSIZE)*FIELDWIDTH+5, (BOXSIZE+GAPSIZE)*FIELDHEIGHT+5))
    
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                left, top = get_left_top_xy(box_x, box_y)
                pygame.draw.rect(self._display_surface, BOXCOLOR_REV, (left, top, BOXSIZE, BOXSIZE))
    
        self._display_surface.blit(RESET_SURF, RESET_RECT)
        self._display_surface.blit(SHOW_SURF, SHOW_RECT)
        
        self.draw_mines_numbers()
        self.draw_covers()

    def draw_mines_numbers(self):
        # draws mines and numbers onto GUI
        # field should have mines and numbers
        half = int(BOXSIZE*0.5) 
        quarter = int(BOXSIZE*0.25)
        eighth = int(BOXSIZE*0.125)
        
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                left, top = get_left_top_xy(box_x, box_y)
                center_x, center_y = get_center_xy(box_x, box_y)
                if self.mine_field[box_x][box_y] == MINE:
                    pygame.draw.circle(self._display_surface, MINECOLOR, (left+half, top+half), quarter)
                    pygame.draw.circle(self._display_surface, WHITE, (left+half, top+half), eighth)
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+eighth, top+half), (left+half+quarter+eighth, top+half))
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+half, top+eighth), (left+half, top+half+quarter+eighth))
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+quarter, top+quarter), (left+half+quarter, top+half+quarter))
                    pygame.draw.line(self._display_surface, MINECOLOR, (left+quarter, top+half+quarter), (left+half+quarter, top+quarter))
                else: 
                    for i in range(1,9):
                        if self.mine_field[box_x][box_y] == i:
                            if i in range(1,3):
                                text_color = TEXTCOLOR_1
                            else:
                                text_color = TEXTCOLOR_2
                            draw_text(str(i), BASICFONT, text_color, self._display_surface, center_x, center_y)
                            
    def draw_covers(self):
        # uses revealedBox FIELDWIDTH x FIELDHEIGHT data structure to determine whether to draw box covering mine/number
        # draw red cover instead of gray cover over marked mines
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                if not self.revealed_boxes[box_x][box_y]:
                    left, top = get_left_top_xy(box_x, box_y)
                    if [box_x, box_y] in self.marked_mines:
                        pygame.draw.rect(self._display_surface, MINEMARK_COV, (left, top, BOXSIZE, BOXSIZE))
                    else:
                        pygame.draw.rect(self._display_surface, BOXCOLOR_COV, (left, top, BOXSIZE, BOXSIZE))
                        
    def highlight_box(self, box_x, box_y):
        # highlight box when mouse hovers over it
        left, top = get_left_top_xy(box_x, box_y)
        pygame.draw.rect(self._display_surface, HILITECOLOR, (left, top, BOXSIZE, BOXSIZE), 4)
    
    
    def highlight_button(self, butRect):
        # highlight button when mouse hovers over it
        linewidth = 4
        pygame.draw.rect(self._display_surface, HILITECOLOR, (butRect.left-linewidth, butRect.top-linewidth, butRect.width+2*linewidth, butRect.height+2*linewidth), linewidth)

    def is_game_won(self):
        """Checks if player has revealed all boxes"""
        not_mine_count = 0
    
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                if self.revealed_boxes[box_x][box_y] == True:
                    if self.mine_field[box_x][box_y] != MINE:
                        not_mine_count += 1
    
        if not_mine_count >= (FIELDWIDTH*FIELDHEIGHT) - MINESTOTAL:
            return True
        else:
            return False
        
    def _save_turn(self):
        info = self.available_info()
            
        score = 0
        for col in info:
            score += sum(i != MINE and i != -1 for i in col)
        
        self.database.append({
            "turn": info,
            "score": score,
        })
#         print(self.database[-1])

    def available_info(self):
        info = []
        
        for x in range(len(self.mine_field)):
            line = []
            for y in range(len(self.mine_field[x])):
                if [x,y] in self.marked_mines:
                    line.append(-2)
                else:
                    try:
                        line.append(int(self.mine_field[x][y]) if self.revealed_boxes[x][y] else -1)
                    except:
                        line.append('X')
            info.append(line)
    
#         debug_board(info, 'info')
        return info

    def show_numbers(self, box_x, box_y, zero_list_xy=[]):
        # modifies revealedBox data structure if chosen box_x & box_y is 0
        # show all boxes using recursion
        self.revealed_boxes[box_x][box_y] = True
        reveal_adjacent_boxes(self.revealed_boxes, box_x, box_y)
        for i,j in get_adjacent_boxes_xy(box_x, box_y):
            if self.mine_field[i][j] == 0 and [i,j] not in zero_list_xy:
                zero_list_xy.append([i,j])
                self.show_numbers(i, j, zero_list_xy)

    def show_mines(self):     
        # modifies revealedBox data structure if chosen box_x & box_y is [X] 
        for i in range(FIELDWIDTH):
            for j in range(FIELDHEIGHT):
                if self.mine_field[i][j] == MINE:
                    self.revealed_boxes[i][j] = True


def main():
    tries = 0
    
    minesweeper = Minesweeper()
    
    # stores XY of mouse events
    mouse_x = 0
    mouse_y = 0
    
    while True:
        has_game_ended = False

        # set up data structures and lists
        minesweeper.new_game()
        
        tries +=1
        print(tries)

        # main game loop
        while not has_game_ended:

            # check for quit function
            check_for_termination()

            # initialize input booleans
            mouse_clicked = False
            space_pressed = False

            minesweeper.draw_field()

            # event handling loop
            for event in pygame.event.get():
                
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    terminate()
                elif event.type == MOUSEMOTION:
                    mouse_x, mouse_y = event.pos
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == LEFT_CLICK:
                        mouse_x, mouse_y = event.pos
                        mouse_clicked = True
                    if event.button == RIGHT_CLICK:
                        space_pressed = True

                elif event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        space_pressed = True
                elif event.type == KEYUP:
                    if event.key == K_SPACE:
                        space_pressed = False
  
            # determine boxes at clicked areas
            box_x, box_y = get_box_at_pixel(mouse_x, mouse_y)
            
            if AI_ENABLED:
                info = minesweeper.available_info()
            
                for s in AI_mark_squares(info):
                    minesweeper.marked_mines.append([s[0], s[1]])
    
                safe_squares = AI_reveal_safe_squares(info)
                if safe_squares:
                    box_x, box_y = safe_squares[0][0], safe_squares[0][1]
                    mouse_clicked = True
                else:
                    box_x, box_y = (random.choice(range(FIELDWIDTH)), random.choice(range(FIELDHEIGHT)))
                    mouse_clicked = True

            # mouse not over a box in field
            if (box_x, box_y) == (None, None):

                # check if reset box is clicked
                if RESET_RECT.collidepoint(mouse_x, mouse_y):
                    minesweeper.highlight_button(RESET_RECT)
                    if mouse_clicked: 
                        minesweeper.new_game()

                # check if show box is clicked
                if SHOW_RECT.collidepoint(mouse_x, mouse_y):
                    minesweeper.highlight_button(SHOW_RECT)
                    if mouse_clicked:
                        minesweeper.revealed_boxes = blank_revealed_box_data(True)

            # mouse currently over box in field
            else:
                # highlight unrevealed box
                if not minesweeper.revealed_boxes[box_x][box_y]: 
                    minesweeper.highlight_box(box_x, box_y)

                    # mark mines
                    if space_pressed:
                        minesweeper.marked_mines.append([box_x, box_y])
                        
                    # reveal clicked boxes
                    if mouse_clicked:
                        minesweeper.revealed_boxes[box_x][box_y] = True
                                               
                        if minesweeper.is_game_won():
                            print('WIN!!!')
                            has_game_ended = True
                        
                        minesweeper._save_turn()

                        # when 0 is revealed, show relevant boxes
                        if minesweeper.mine_field[box_x][box_y] == 0:
                            minesweeper.show_numbers(box_x, box_y)

                        # when mine is revealed, show mines
                        if minesweeper.mine_field[box_x][box_y] == MINE:
                            minesweeper.show_mines()
                            has_game_ended = True
                
            # redraw screen, wait clock tick
            pygame.display.update()
            minesweeper.clock.tick(FPS)


def blank_field():
    """Creates blank FIELDWIDTH x FIELDHEIGHT data structure"""
    field = []
    for _ in range(FIELDWIDTH):
        field.append([0 for _ in range(FIELDHEIGHT)]) 
            
    return field


def get_random_minefield(): 
    """Places mines in FIELDWIDTH x FIELDHEIGHT data structure"""
    field = blank_field()
    mine_count = 0
    xy = [] 
    while mine_count < MINESTOTAL: 
        x = random.randint(0, FIELDWIDTH-1)
        y = random.randint(0, FIELDHEIGHT-1)
        xy.append([x, y]) 
        if xy.count([x, y]) > 1: 
            xy.remove([x, y]) 
        else: 
            field[x][y] = MINE 
            mine_count += 1
    
    place_numbers(field)
    return field


def is_there_mine(field, x, y): 
    # checks if mine is located at specific box on field
    return field[x][y] == MINE


def place_numbers(field): 
    # places numbers in FIELDWIDTH x FIELDHEIGHT data structure
    # requires field with mines as input
    for x in range(FIELDWIDTH):
        for y in range(FIELDHEIGHT):
            if not is_there_mine(field, x, y):
                count = 0
                if x != 0: 
                    if is_there_mine(field, x-1, y):
                        count += 1
                    if y != 0: 
                        if is_there_mine(field, x-1, y-1):
                            count += 1
                    if y != FIELDHEIGHT-1: 
                        if is_there_mine(field, x-1, y+1):
                            count += 1
                if x != FIELDWIDTH-1: 
                    if is_there_mine(field, x+1, y):
                        count += 1
                    if y != 0: 
                        if is_there_mine(field, x+1, y-1):
                            count += 1
                    if y != FIELDHEIGHT-1: 
                        if is_there_mine(field, x+1, y+1):
                            count += 1
                if y != 0: 
                    if is_there_mine(field, x, y-1):
                        count += 1
                if y != FIELDHEIGHT-1: 
                    if is_there_mine(field, x, y+1):
                        count += 1
                field[x][y] = count


def blank_revealed_box_data(val):
    # returns FIELDWIDTH x FIELDHEIGHT data structure different from the field data structure
    # each item in data structure is boolean (val) to show whether box at those fieldwidth & fieldheight coordinates should be revealed
    revealed_boxes = []
    for _ in range(FIELDWIDTH):
        revealed_boxes.append([val] * FIELDHEIGHT)
    return revealed_boxes


def reveal_adjacent_boxes(revealed_boxes, box_x, box_y):
    # modifies revealed_boxes data structure so that all adjacent boxes to (box_x, box_y) are set to True
    if box_x != 0: 
        revealed_boxes[box_x-1][box_y] = True
        if box_y != 0: 
            revealed_boxes[box_x-1][box_y-1] = True
        if box_y != FIELDHEIGHT-1: 
            revealed_boxes[box_x-1][box_y+1] = True
    if box_x != FIELDWIDTH-1:
        revealed_boxes[box_x+1][box_y] = True
        if box_y != 0: 
            revealed_boxes[box_x+1][box_y-1] = True
        if box_y != FIELDHEIGHT-1: 
            revealed_boxes[box_x+1][box_y+1] = True
    if box_y != 0: 
        revealed_boxes[box_x][box_y-1] = True
    if box_y != FIELDHEIGHT-1: 
        revealed_boxes[box_x][box_y+1] = True
        

def get_adjacent_boxes_xy(box_x, box_y):
    # get box XY coordinates for all adjacent boxes to (box_x, box_y)
    adjacent_boxes_xy = []

    if box_x != 0:
        adjacent_boxes_xy.append([box_x-1,box_y])
        if box_y != 0:
            adjacent_boxes_xy.append([box_x-1,box_y-1])
        if box_y != FIELDHEIGHT-1:
            adjacent_boxes_xy.append([box_x-1,box_y+1])
    if box_x != FIELDWIDTH-1: 
        adjacent_boxes_xy.append([box_x+1,box_y])
        if box_y != 0:
            adjacent_boxes_xy.append([box_x+1,box_y-1])
        if box_y != FIELDHEIGHT-1:
            adjacent_boxes_xy.append([box_x+1,box_y+1])
    if box_y != 0:
        adjacent_boxes_xy.append([box_x,box_y-1])
    if box_y != FIELDHEIGHT-1:
        adjacent_boxes_xy.append([box_x,box_y+1])

    return adjacent_boxes_xy


def draw_text(text, font, color, surface, x, y):  
    # function to easily draw text and also return object & rect pair
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.centerx = x
    textrect.centery = y
    surface.blit(textobj, textrect)


def draw_button(text, color, bgcolor, center_x, center_y):
    # similar to draw_text but text has bg color and returns obj & rect
    butSurf = BASICFONT.render(text, True, color, bgcolor)
    butRect = butSurf.get_rect()
    butRect.centerx = center_x
    butRect.centery = center_y

    return (butSurf, butRect)


def get_left_top_xy(box_x, box_y):
    # get left & top coordinates for drawing mine boxes
    left = XMARGIN + box_x*(BOXSIZE+GAPSIZE)
    top = YMARGIN + box_y*(BOXSIZE+GAPSIZE)
    return left, top


def get_center_xy(box_x, box_y):
    # get center coordinates for drawing mine boxes
    center_x = XMARGIN + BOXSIZE/2 + box_x*(BOXSIZE+GAPSIZE)
    center_y = YMARGIN + BOXSIZE/2 + box_y*(BOXSIZE+GAPSIZE)
    return center_x, center_y


def get_box_at_pixel(x, y):
    # gets coordinates of box at mouse coordinates
    for box_x in range(FIELDWIDTH):
        for box_y in range(FIELDHEIGHT):
            left, top = get_left_top_xy(box_x, box_y)
            boxRect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
            if boxRect.collidepoint(x, y):
                return (box_x, box_y)
    return (None, None)


def terminate():
    """Simple function to exit game"""
    pygame.quit()
    sys.exit()


def check_for_termination():
    """Check if QUIT or ESCAPE key is pressed"""
    if len(pygame.event.get(QUIT)) > 0:
        terminate()
        
    keyUpEvents = pygame.event.get(KEYUP)
    
    if len(keyUpEvents) > 0 and keyUpEvents[0].key == K_ESCAPE:
        terminate()


def debug_board(board, title=None):
    if title:
        print(title)
    for y in range(len(board)):
        print([board[x][y] for x in range(len(board[y]))])
    print()


def neighbour_squares(square, min_x=0, max_x=FIELDWIDTH-1, min_y=0, max_y=FIELDHEIGHT-1):
    neighbours = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            neighbours.append([square[0]+i, square[1]+j])
    neighbours.remove(square)
    
    if min_x is not None:
        neighbours = [item for item in neighbours if item[0] >= min_x]
     
    if max_x is not None:
        neighbours = [item for item in neighbours if item[0] <= max_x]
                 
    if min_y is not None:
        neighbours = [item for item in neighbours if item[1] >= min_y]
     
    if max_y is not None:
        neighbours = [item for item in neighbours if item[1] <= max_y]
    
    return neighbours


def hidden_neighbours(square, available_info):
    hidden_squares = []
    for neighbour in neighbour_squares(square):
        x = neighbour[0]
        y = neighbour[1]
        if available_info[x][y] == -1:
            hidden_squares.append(neighbour)
    return hidden_squares


def marked_neighbours(square, available_info):
    marked_squares = []
    for neighbour in neighbour_squares(square):
        x = neighbour[0]
        y = neighbour[1]
        if available_info[x][y] == -2:
            marked_squares.append(neighbour)
    return marked_squares


def AI_mark_squares(available_info):
    marked = []
    for x in range(len(available_info)):
        for y in range(len(available_info[x])):
            neighbours = hidden_neighbours([x, y], available_info)
            neighbours.extend(marked_neighbours([x, y], available_info))
            if available_info[x][y] == len(neighbours):
                marked.extend(neighbours)
    return marked


def AI_reveal_safe_squares(available_info):
    revealed = []
    for x in range(len(available_info)):
        for y in range(len(available_info[x])):
            marked = marked_neighbours([x, y], available_info)
            if available_info[x][y] == len(marked):
                revealed.extend(hidden_neighbours([x, y], available_info))
    return revealed


if __name__ == '__main__':
    main()
