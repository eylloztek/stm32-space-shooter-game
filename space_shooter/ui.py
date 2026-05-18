# ui.py - User interface components for the STM32 ADXL345 Space Shooter game, including background and screen overlays

import pygame

from settings import *
from assets import get_sprite


class ScrollingBackground:
    def __init__(self):
        self.y = 0

    def update(self):
        self.y += BACKGROUND_SCROLL_SPEED

        if self.y >= HEIGHT:
            self.y = 0

    def draw(self, screen, sprites):
        background = sprites.get("background")

        if background is None:
            screen.fill((15, 15, 25))
            return

        y = int(self.y)

        # first background, then second to create scrolling effect
        screen.blit(background, (0, y))

        # second background, placed on top of the first
        screen.blit(background, (0, y - HEIGHT))

def draw_background(screen, sprites):
    if sprites["background"] is not None:
        screen.blit(sprites["background"], (0, 0))
    else:
        screen.fill((15, 15, 25))


def draw_start_screen(screen, sprites, font):
    draw_background(screen, sprites)

    title = font.render(
        "STM32 ADXL345 SPACE SHOOTER",
        True,
        (255, 255, 255)
    )

    start_text = font.render(
        "Press external CTRL button to start",
        True,
        (255, 255, 120)
    )

    control_text = font.render(
        "Tilt ADXL345 to move, external button to fire",
        True,
        (200, 200, 200)
    )

    screen.blit(
        title,
        (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 80)
    )

    screen.blit(
        start_text,
        (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2 - 25)
    )

    screen.blit(
        control_text,
        (WIDTH // 2 - control_text.get_width() // 2, HEIGHT // 2 + 25)
    )

    pygame.display.flip()


def draw_pause_screen(screen, sprites, font, draw_game_callback):
    draw_game_callback(flip=False)

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    pause_text = font.render("PAUSED", True, (255, 255, 255))
    resume_text = font.render("Press P or CTRL to resume", True, (200, 200, 200))

    screen.blit(
        pause_text,
        (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 40)
    )

    screen.blit(
        resume_text,
        (WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2 + 10)
    )

    pygame.display.flip()


def draw_game_over_screen(screen, sprites, font, score, draw_game_callback):
    draw_game_callback(flip=False)

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    game_over_text = font.render("GAME OVER", True, (255, 80, 80))
    score_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
    restart_text = font.render("Press R to restart", True, (200, 200, 200))

    screen.blit(
        game_over_text,
        (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60)
    )

    screen.blit(
        score_text,
        (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 20)
    )

    screen.blit(
        restart_text,
        (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 25)
    )

    pygame.display.flip()


def draw_win_screen(screen, sprites, font, score, draw_game_callback):
    draw_game_callback(flip=False)

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    win_text = font.render("YOU WIN!", True, (100, 255, 120))
    score_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
    restart_text = font.render("Press R to restart", True, (200, 200, 200))

    screen.blit(
        win_text,
        (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 60)
    )

    screen.blit(
        score_text,
        (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 20)
    )

    screen.blit(
        restart_text,
        (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 25)
    )

    pygame.display.flip()


def draw_game_ui(
    screen,
    sprites,
    font,
    small_font,
    player,
    serial_controller,
    score,
    difficulty_level
):
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    level_text = font.render(f"Level: {difficulty_level}", True, (255, 255, 255))

    screen.blit(score_text, (20, 20))
    screen.blit(level_text, (20, 50))

    # Lives
    for i in range(player.lives):
        screen.blit(sprites["heart"], (20 + i * 34, 85))

    # Shield status
    shield_label = font.render("Shield", True, (255, 255, 255))
    screen.blit(shield_label, (20, 125))

    shield_icon = get_sprite(sprites["shield_powerup"], speed_ms=120)

    if shield_icon is not None:
        if player.shield_active:
            screen.blit(shield_icon, (110, 120))
        else:
            disabled_icon = shield_icon.copy()
            disabled_icon.set_alpha(70)
            screen.blit(disabled_icon, (110, 120))

    # ADXL debug
    adxl_text = font.render(
        f"X:{serial_controller.accel_x} Y:{serial_controller.accel_y}",
        True,
        (200, 200, 200)
    )
    screen.blit(adxl_text, (20, 165))

    if not serial_controller.serial_ok:
        serial_text = small_font.render(
            "Serial disconnected",
            True,
            (255, 120, 80)
        )
        screen.blit(serial_text, (20, HEIGHT - 30))