# Save as badminton_game.py and run with: python badminton_game.py
# Controls:
#   Left racket: W / S
#   Right racket: Up / Down
#   Serve: Space (when serving)
#   After a win: R to restart, ESC to quit

import pygame
import sys
import random

pygame.init()
pygame.font.init()

# --- Settings ---
WIDTH, HEIGHT = 900, 520
FPS = 60
SCORE_TO_WIN = 5

RACKET_WIDTH = 12
RACKET_HEIGHT = 90
SHUTTLE_RADIUS = 6

NET_WIDTH = 6
NET_HEIGHT = 140

WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
GREEN = (30, 160, 70)
BLUE = (50, 120, 200)
RED = (200, 60, 60)
GRAY = (200, 200, 200)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Badminton (demo)")
clock = pygame.time.Clock()

large_font = pygame.font.SysFont(None, 48)
font = pygame.font.SysFont(None, 26)


class Racket:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.width = RACKET_WIDTH
        self.height = RACKET_HEIGHT
        self.color = color
        self.score = 0
        self.speed = 6

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect())

    def move(self, dy):
        self.y += dy
        # clamp
        if self.y < 0:
            self.y = 0
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height


class Shuttle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.in_play = False

    def draw(self, surf):
        pygame.draw.circle(surf, BLACK, (int(self.x), int(self.y)), SHUTTLE_RADIUS)

    def update(self):
        # simple gravity-like downward pull (shuttlecock effect is more complex; this is enough for demo)
        if self.in_play:
            self.vel_y += 0.18  # gravity
            self.x += self.vel_x
            self.y += self.vel_y

            # bounce a bit off the top if it goes above screen
            if self.y < SHUTTLE_RADIUS:
                self.y = SHUTTLE_RADIUS
                self.vel_y = -self.vel_y * 0.4

            # small damping if too slow
            if abs(self.vel_x) < 0.3 and abs(self.vel_y) < 0.3:
                self.in_play = False


# Utility / game functions
def draw_court(surf):
    surf.fill(GREEN)
    # mid-line (net area)
    net_x = WIDTH // 2
    pygame.draw.line(surf, WHITE, (0, HEIGHT - 2), (WIDTH, HEIGHT - 2), 4)  # baseline
    # center line
    pygame.draw.line(surf, WHITE, (net_x, HEIGHT // 2 - NET_HEIGHT // 2),
                     (net_x, HEIGHT // 2 + NET_HEIGHT // 2), NET_WIDTH)


def draw_ui():
    left_text = font.render(f"Left: {left.score}", True, BLACK)
    right_text = font.render(f"Right: {right.score}", True, BLACK)
    screen.blit(left_text, (40, 12))
    screen.blit(right_text, (WIDTH - 40 - right_text.get_width(), 12))
    instr = font.render("W/S = Left | Up/Down = Right | Space = Serve", True, BLACK)
    screen.blit(instr, (WIDTH // 2 - instr.get_width() // 2, 12))


def check_racket_collision(racket: Racket, shuttle: Shuttle):
    if not shuttle.in_play:
        return

    r = racket.rect()
    # circle-rect collision (approx): check if shuttle center is inside racket rect
    if r.collidepoint(shuttle.x, shuttle.y):
        # Determine which side we've hit and set appropriate X velocity
        # If it's left racket, send shuttle to the right; if right racket, send to the left
        if racket.x < WIDTH // 2:
            # left racket
            shuttle.vel_x = max(5.0, abs(shuttle.vel_x) + 2.5)
            shuttle.x = racket.x + racket.width + SHUTTLE_RADIUS + 1
        else:
            # right racket
            shuttle.vel_x = -max(5.0, abs(shuttle.vel_x) + 2.5)
            shuttle.x = racket.x - SHUTTLE_RADIUS - 1

        # change vertical speed based on where the shuttle hit the racket
        rel = (shuttle.y - (racket.y + racket.height / 2)) / (racket.height / 2)
        shuttle.vel_y += rel * 4.0

        # small random tweak
        shuttle.vel_y += random.uniform(-0.8, 0.8)
        shuttle.in_play = True


def check_net_collision(shuttle: Shuttle):
    net_rect = pygame.Rect(WIDTH // 2 - NET_WIDTH // 2,
                           HEIGHT // 2 - NET_HEIGHT // 2,
                           NET_WIDTH,
                           NET_HEIGHT)
    if net_rect.collidepoint(shuttle.x, shuttle.y):
        # if it hits the net, reduce horizontal speed and bounce down
        shuttle.vel_x *= -0.35
        shuttle.vel_y = -abs(shuttle.vel_y) * 0.6
        shuttle.in_play = True


def check_ground(shuttle: Shuttle):
    # returns: None if not landed; -1 if left player scores, 1 if right player scores
    if shuttle.y >= HEIGHT - SHUTTLE_RADIUS - 2:  # touched ground / baseline
        # If shuttle lands on right half -> left player scores (-1)
        return -1 if shuttle.x > WIDTH // 2 else 1
    # also if shuttle goes completely off left/right side (rare here) treat as point
    if shuttle.x < -50:
        return 1
    if shuttle.x > WIDTH + 50:
        return -1
    return None


# Create players and shuttle
left = Racket(24, HEIGHT // 2 - RACKET_HEIGHT // 2, BLUE)
right = Racket(WIDTH - 24 - RACKET_WIDTH, HEIGHT // 2 - RACKET_HEIGHT // 2, RED)
shuttle = Shuttle()

# serving: -1 means left will serve, 1 means right will serve
serve_direction = -1
serving = True

def position_shuttle_for_serving():
    # Put shuttle near the server's racket when serving
    if serve_direction == -1:
        shuttle.x = left.x + left.width + SHUTTLE_RADIUS + 8
        shuttle.y = left.y + left.height / 2
    else:
        shuttle.x = right.x - SHUTTLE_RADIUS - 8
        shuttle.y = right.y + right.height / 2
    shuttle.vel_x = 0.0
    shuttle.vel_y = 0.0
    shuttle.in_play = False


position_shuttle_for_serving()

# Main loop
while True:
    clock.tick(FPS)

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            # serve with Space
            if event.key == pygame.K_SPACE and serving and not shuttle.in_play:
                # Put some initial velocity depending on server
                speed_x = 6.5
                speed_y = -2.0 + random.uniform(-1.0, 0.5)
                if serve_direction == -1:
                    shuttle.vel_x = speed_x
                else:
                    shuttle.vel_x = -speed_x
                shuttle.vel_y = speed_y
                shuttle.in_play = True
                serving = False

    # Player controls
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        left.move(-left.speed)
    if keys[pygame.K_s]:
        left.move(left.speed)
    if keys[pygame.K_UP]:
        right.move(-right.speed)
    if keys[pygame.K_DOWN]:
        right.move(right.speed)

    # Update shuttle
    shuttle.update()

    # Collisions
    check_racket_collision(left, shuttle)
    check_racket_collision(right, shuttle)
    check_net_collision(shuttle)

    # Ground / out-of-bounds check -> scoring
    point = check_ground(shuttle)
    if point is not None:
        # point: -1 left scores, 1 right scores
        if point == -1:
            left.score += 1
            winner = "Left"
            serve_direction = -1  # winner serves next
        else:
            right.score += 1
            winner = "Right"
            serve_direction = 1

        # reset shuttle and go to serving state
        shuttle.reset()
        serving = True
        position_shuttle_for_serving()

    # Win check
    if left.score >= SCORE_TO_WIN or right.score >= SCORE_TO_WIN:
        winner_name = "Left Player" if left.score > right.score else "Right Player"

        # draw final screen
        draw_court(screen)
        left.draw(screen)
        right.draw(screen)
        shuttle.draw(screen)

        ui_text = large_font.render(f"{winner_name} wins!", True, BLACK)
        screen.blit(ui_text, (WIDTH // 2 - ui_text.get_width() // 2,
                              HEIGHT // 2 - ui_text.get_height() // 2))

        sub = font.render("Press R to play again or ESC to quit.", True, BLACK)
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.flip()

        # wait for reset or quit
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_r:
                        left.score = 0
                        right.score = 0
                        shuttle.reset()
                        serving = True
                        serve_direction = -1
                        position_shuttle_for_serving()
                        waiting = False
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            clock.tick(FPS)
        # resume main loop
        continue

    # Draw everything
    draw_court(screen)
    left.draw(screen)
    right.draw(screen)

    # if serving, position shuttle near server racket
    if not shuttle.in_play and serving:
        position_shuttle_for_serving()
        shuttle.draw(screen)
    else:
        shuttle.draw(screen)

    draw_ui()
    pygame.display.flip()
