from random import randrange as rand
import pygame
import sys

# The configuration
CELL_SIZE = 32
COLS = 10
ROWS = 22
MAX_FPS = 60
FONT_SIZE = int(CELL_SIZE / 8 * 5)

colors = {"black": (0, 0, 0),
          "gray": (35, 35, 35),
          "t": (80, 0, 160),
          "t_grid": (100, 0, 200),
          "s": (50, 200, 50),
          "s_grid": (100, 250, 100),
          "z": (200, 0, 0),
          "z_grid": (255, 0, 0),
          "j": (0, 0, 200),
          "j_grid": (0, 0, 255),
          "l": (200, 80, 0),
          "l_grid": (255, 100, 0),
          "i": (0, 100, 200),
          "i_grid": (0, 150, 255),
          "o": (200, 200, 0),
          "o_grid": (255, 255, 0)}

# Define the shapes of the single parts
shapes = [[[0, 2, 0],
           [2, 2, 2],
           [0, 0, 0]],

          [[0, 4, 4],
           [4, 4, 0],
           [0, 0, 0]],

          [[6, 6, 0],
           [0, 6, 6],
           [0, 0, 0]],

          [[8, 0, 0],
           [8, 8, 8],
           [0, 0, 0]],

          [[0, 0, 10],
           [10, 10, 10],
           [0, 0, 0]],

          [[0, 0, 0, 0],
           [12, 12, 12, 12],
           [0, 0, 0, 0],
           [0, 0, 0, 0]],

          [[14, 14],
           [14, 14]]]


class Stone:
    def __init__(self, shape):
        self.shape = shape
        self.x = COLS + 1
        self.y = 1

    def rotate(self):
        self.shape = [[self.shape[y][x] for y in range(len(self.shape))]
                      for x in range(len(self.shape[0]) - 1, -1, -1)]

    def check_collision(self, board):
        for cy, row in enumerate(self.shape):
            for cx, cell in enumerate(row):
                try:
                    if cell and board[cy + self.y][cx + self.x + 1]:
                        return True
                except IndexError:
                    return True
        return False


class Board:
    def __init__(self):
        self.shape = [[1] + [0 for x in range(COLS)] for y in range(ROWS)]
        self.shape += [[2 for x in range(COLS + 1)]]
        self.x = -1
        self.y = 0

    def remove_row(self, row):
        del self.shape[row]
        self.shape = [[1] + [0 for x in range(COLS)]] + self.shape

    def join_stone(self, stone):
        for cy, row in enumerate(stone.shape):
            for cx, val in enumerate(row):
                if val:
                    self.shape[cy + stone.y - 1][cx + stone.x + 1] += val


class Tetris:
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(250, 25)
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000)

        self.width = CELL_SIZE * (COLS + 6)
        self.height = CELL_SIZE * ROWS
        self.rlim = CELL_SIZE * COLS

        self.default_font = pygame.font.Font(pygame.font.get_default_font(), FONT_SIZE)
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.gameover = True

        self.key_actions = {"ESCAPE": self.quit,
                            "LEFT": lambda: self.move(-1),
                            "RIGHT": lambda: self.move(+1),
                            "DOWN": lambda: self.drop(True),
                            "UP": self.rotate_stone,
                            "p": self.toggle_pause,
                            "SPACE": self.start_game,
                            "RETURN": self.insta_drop,
                            "LSHIFT": self.hold}

    def new_stone(self):
        self.stone = self.next_stone
        self.stone.x = int(COLS / 2 - len(self.stone.shape[0]) / 2)
        self.stone.y = 0
        self.next_stone = Stone(shapes[rand(len(shapes))])

        if self.stone.check_collision(self.board.shape):
            self.gameover = True

        if self.ai:
            self.ai()

    def disp_msg(self, msg, pos):
        x, y = pos
        for line in msg.splitlines():
            self.screen.blit(self.default_font.render(line, False, (255, 255, 255), (0, 0, 0)), (x, y))
            y += FONT_SIZE + 2

    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image = self.default_font.render(line, False, (255, 255, 255), (0, 0, 0))

            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2

            self.screen.blit(msg_image,
                             (self.width // 2 - msgim_center_x,
                              self.height // 2 - msgim_center_y + i * 22))

    def add_cl_lines(self, n):
        linescores = [0, 40, 100, 300, 1200]
        self.lines += n
        self.score += linescores[n] * self.level
        if self.lines >= self.level * 6:
            self.level += 1
            newdelay = 1000 - 50 * (self.level - 1)
            newdelay = 100 if newdelay < 100 else newdelay
            pygame.time.set_timer(pygame.USEREVENT + 1, newdelay)

    def move(self, delta_x):
        if not self.gameover and not self.paused:
            self.stone.x += delta_x
            if self.stone.check_collision(self.board.shape):
                self.stone.x -= delta_x

    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()

    def drop(self, manual):
        if not self.gameover and not self.paused:
            self.score += 1 if manual else 0
            self.stone.y += 1
            if self.stone.check_collision(self.board.shape):
                self.board.join_stone(self.stone)
                self.new_stone()
                cleared_rows = 0
                while True:
                    for i, row in enumerate(self.board.shape[:-1]):
                        if 0 not in row:
                            self.board.remove_row(i)
                            cleared_rows += 1
                            break
                    else:
                        break
                self.add_cl_lines(cleared_rows)
                return True
        return False

    def insta_drop(self):
        if not self.gameover and not self.paused:
            while not self.drop(True):
                pass

    def rotate_stone(self):
        if not self.gameover and not self.paused:
            self.stone.rotate()
            if self.stone.check_collision(self.board.shape):
                for i in range(3):
                    self.stone.rotate()

    def draw_background(self):
        background = [[1 if x % 2 == y % 2 else 0 for x in range(COLS)] for y in range(ROWS)]
        for y, row in enumerate(background):
            for x, val in enumerate(row):
                if val:
                    pygame.draw.rect(self.screen, colors[list(colors.keys())[val]],
                                     pygame.Rect(x * CELL_SIZE, y * CELL_SIZE,
                                                 CELL_SIZE, CELL_SIZE), 0)

    def draw(self, part, predicted=False):
        for y, row in enumerate(part.shape):
            for x, val in enumerate(row):
                if val:
                    if predicted:
                        pygame.draw.rect(self.screen, (colors[list(colors.keys())[val]][0] / 2,
                                                       colors[list(colors.keys())[val]][1] / 2,
                                                       colors[list(colors.keys())[val]][2] / 2),
                                         pygame.Rect((part.x + x) * CELL_SIZE,
                                                     (part.y + y) * CELL_SIZE,
                                                     CELL_SIZE, CELL_SIZE), 0)
                        pygame.draw.rect(self.screen, (colors[list(colors.keys())[val + 1]][0] / 2,
                                                       colors[list(colors.keys())[val + 1]][1] / 2,
                                                       colors[list(colors.keys())[val + 1]][2] / 2),
                                         pygame.Rect((part.x + x) * CELL_SIZE,
                                                     (part.y + y) * CELL_SIZE,
                                                     CELL_SIZE, CELL_SIZE), int(CELL_SIZE / 32))
                    else:
                        pygame.draw.rect(self.screen, colors[list(colors.keys())[val]],
                                         pygame.Rect((part.x + x) * CELL_SIZE,
                                                     (part.y + y) * CELL_SIZE,
                                                     CELL_SIZE, CELL_SIZE), 0)
                        pygame.draw.rect(self.screen, colors[list(colors.keys())[val + 1]],
                                         pygame.Rect((part.x + x) * CELL_SIZE,
                                                     (part.y + y) * CELL_SIZE,
                                                     CELL_SIZE, CELL_SIZE), int(CELL_SIZE / 32))

    def draw_predicted(self):
        predicted_stone = Stone(self.stone.shape)
        predicted_stone.x = self.stone.x
        predicted_stone.y = self.stone.y
        while not predicted_stone.check_collision(self.board.shape):
            predicted_stone.y += 1
        predicted_stone.y -= 1
        self.draw(predicted_stone, True)

    def toggle_pause(self):
        self.paused = not self.paused

    def hold(self):
        self.hold, self.stone = self.stone, self.hold
        self.stone.x = self.hold.x
        self.stone.y = self.hold.y
        self.hold.x = COLS + 1
        self.hold.y = 5
        if self.stone.shape == [[0], [0]]:
            self.new_stone()

    def start_game(self):
        if self.gameover:
            self.board = Board()
            self.level = 1
            self.score = 0
            self.lines = 0
            self.gameover = False
            self.paused = False
            self.next_stone = Stone(shapes[rand(len(shapes))])
            self.new_stone()
            self.hold = Stone([[0], [0]])
            self.run()

    def height_sum(self):
        height = 0
        for x in range(COLS + 1):
            for y in range(ROWS):
                if self.board.shape[y][x] >= 2:
                    height += ROWS - y
                    break
        return height

    def completed_lines(self):
        line = 0
        for row in self.board.shape[:-1]:
            if 0 not in row:
                line += 1
        return line

    def bumpiness(self):
        bumpiness = 0
        last_col = 0
        for x in range(COLS + 1):
            for y in range(ROWS + 1):
                if self.board.shape[y][x] >= 2:
                    if not last_col:
                        last_col = ROWS - y
                    bumpiness += abs(ROWS - y - last_col)
                    last_col = ROWS - y
                    break
        return bumpiness

    def hole(self):
        hole = 0
        for x in range(COLS + 1):
            for y in range(1, ROWS):
                if not self.board.shape[y][x] and self.board.shape[y - 1][x]:
                    hole += 1
                    break
        return hole

    def ai(self):
        a = -0.510066
        b = 0.760666
        c = -0.35663
        d = -0.184483
        score = a * self.height_sum() + b * self.completed_lines() + c * self.hole() + d * self.bumpiness()
        print(score)

    def run(self):
        while 1:
            self.screen.fill((0, 0, 0))
            if self.gameover:
                self.center_msg("""Game Over!\nYour score: %d\nPress space to continue""" % self.score)
            elif self.paused:
                self.center_msg("Paused")
            else:
                pygame.draw.line(self.screen, (255, 255, 255), (self.rlim + 1, 0), (self.rlim + 1, self.height - 1))
                self.disp_msg("Next:", (self.rlim + CELL_SIZE, 2))
                self.disp_msg("Hold:", (self.rlim + CELL_SIZE, 122))
                self.disp_msg("Score: %d\n\nLevel: %d\nLines: %d" % (self.score, self.level, self.lines),
                              (self.rlim + CELL_SIZE, CELL_SIZE * 10))
                self.draw_background()
                self.draw(self.board)
                self.draw_predicted()
                self.draw(self.stone)
                self.draw(self.next_stone)
                self.draw(self.hold)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.drop(False)
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in self.key_actions:
                        if event.key == eval("pygame.K_" + key):
                            self.key_actions[key]()

            pygame.time.Clock().tick(MAX_FPS)


if __name__ == '__main__':
    App = Tetris()
    App.start_game()
    App.ai()
