#main.py - Main game loop and logic for the STM32 ADXL345 Space Shooter game

import pygame
import sys
from settings import *
from game_state import *
from assets import load_assets, asset_path
from serial_comm import SerialController
from player import Player
from bullets import BulletManager
from enemy import EnemyManager
from boss import BossManager
from powerups import PowerupManager
from explosions import ExplosionManager
from audio import AudioManager
from ui import (
    ScrollingBackground,
    draw_start_screen,
    draw_pause_screen,
    draw_game_over_screen,
    draw_win_screen,
    draw_game_ui
)

difficulty_level = 1
last_difficulty_score = 0

enemy_spawn_delay = ENEMY_SPAWN_DELAY
enemy_bullet_speed = ENEMY_BULLET_SPEED

game_state = STATE_START

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("STM32 ADXL345 Space Shooter")
clock = pygame.time.Clock()

font = pygame.font.Font(asset_path("PressStart2P-Regular.ttf"), 14)
small_font = pygame.font.Font(asset_path("PressStart2P-Regular.ttf"), 10)

SPRITES = load_assets()
serial_controller = SerialController()
player = Player()
bullet_manager = BulletManager()
enemy_manager = EnemyManager()
boss_manager = BossManager()
powerup_manager = PowerupManager()
explosion_manager = ExplosionManager()
scrolling_background = ScrollingBackground()
audio_manager = AudioManager()

last_enemy_time = pygame.time.get_ticks()

def handle_ctrl_input():
    global game_state

    if serial_controller.ctrl_pressed != 1:
        return

    if game_state == STATE_START:
        if serial_controller.calibrated == 1:
            reset_game()

    elif game_state == STATE_PLAYING:
        game_state = STATE_PAUSED

    elif game_state == STATE_PAUSED:
        game_state = STATE_PLAYING

    elif game_state == STATE_GAME_OVER or game_state == STATE_WIN:
        reset_game()


def reset_game():
    global score
    global last_enemy_time
    global game_state
    global difficulty_level, last_difficulty_score
    global enemy_spawn_delay, enemy_bullet_speed

    player.reset()
    bullet_manager.reset()
    enemy_manager.reset()
    boss_manager.reset()
    powerup_manager.reset()
    explosion_manager.reset()

    score = 0

    difficulty_level = 1
    last_difficulty_score = 0
    enemy_spawn_delay = ENEMY_SPAWN_DELAY
    enemy_bullet_speed = ENEMY_BULLET_SPEED

    last_enemy_time = pygame.time.get_ticks()

    game_state = STATE_PLAYING

def update_difficulty():
    global difficulty_level
    global enemy_spawn_delay
    global enemy_bullet_speed
    global last_difficulty_score

    if score >= last_difficulty_score + 50:
        difficulty_level += 1
        last_difficulty_score = score

        enemy_spawn_delay = max(
            MIN_ENEMY_SPAWN_DELAY,
            ENEMY_SPAWN_DELAY - difficulty_level * 100
        )

        enemy_bullet_speed = min(
            MAX_ENEMY_BULLET_SPEED,
            ENEMY_BULLET_SPEED + difficulty_level
        )

def set_game_over():
    global game_state
    game_state = STATE_GAME_OVER

def draw_game(flip=True):
    scrolling_background.draw(screen, SPRITES)

    powerup_manager.draw_powerups(screen, SPRITES)

    bullet_manager.draw_enemy_bullets(screen, SPRITES)
    bullet_manager.draw_player_bullets(screen, SPRITES)

    enemy_manager.draw_enemies(screen, SPRITES)
    boss_manager.draw(screen, SPRITES)

    explosion_manager.draw(screen, SPRITES)

    player.draw(screen, SPRITES)

    draw_game_ui(
        screen,
        SPRITES,
        font,
        small_font,
        player,
        serial_controller,
        score,
        difficulty_level
    )

    powerup_manager.draw_powerup_bars(
        screen,
        SPRITES,
        small_font
    )

    if flip:
        pygame.display.flip()


running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_p:
                if game_state == STATE_PLAYING:
                    game_state = STATE_PAUSED
                elif game_state == STATE_PAUSED:
                    game_state = STATE_PLAYING

            if event.key == pygame.K_r:
                if game_state == STATE_GAME_OVER or game_state == STATE_WIN:
                    reset_game()

    serial_controller.read()
    handle_ctrl_input()
    audio_manager.update_music(game_state, boss_manager.active)

    if game_state == STATE_START:
        draw_start_screen(screen, SPRITES, font)

    elif game_state == STATE_PLAYING:
        scrolling_background.update()
        player.update_invincibility()
        update_difficulty()
        boss_manager.update_phase(score, serial_controller)
        powerup_manager.update()
        explosion_manager.update(SPRITES)

        player.update_movement(
            serial_controller.accel_x,
            serial_controller.accel_y
        )
        bullet_manager.handle_fire_input(
            player,
            serial_controller,
            powerup_manager.rapid_fire_active,
            powerup_manager.triple_shot_active,
            audio_manager
        )

        current_time = pygame.time.get_ticks()

        if boss_manager.active:
            active_spawn_delay = enemy_spawn_delay * 3
        else:
            active_spawn_delay = enemy_spawn_delay

        if current_time - last_enemy_time > active_spawn_delay:
            enemy_manager.spawn_enemy(difficulty_level)
            last_enemy_time = current_time

        enemy_manager.update_enemies(
            player,
            serial_controller,
            set_game_over,
            audio_manager
        )
        boss_manager.update(audio_manager)

        bullet_manager.enemy_fire(enemy_manager.enemies, enemy_bullet_speed)
        bullet_manager.mini_boss_fire(
            boss_manager.boss,
            boss_manager.active,
            enemy_bullet_speed
        )

        bullet_manager.update_enemy_bullets()
        bullet_manager.update_player_bullets()


        score += enemy_manager.check_player_bullet_collision(
            bullet_manager,
            explosion_manager.spawn_explosion,
            powerup_manager.spawn_powerup,
            audio_manager
        )
        boss_score_gain, next_state = boss_manager.check_player_bullet_collision(
            bullet_manager,
            explosion_manager.spawn_explosion,
            serial_controller,
            audio_manager
        )

        score += boss_score_gain

        if next_state is not None:
            game_state = next_state

        bullet_manager.check_enemy_bullet_collision(
            player,
            serial_controller,
            set_game_over,
            audio_manager
        )
        score += powerup_manager.check_collision(player, audio_manager)

        draw_game()

    elif game_state == STATE_PAUSED:
        draw_pause_screen(screen, SPRITES, font, draw_game)

    elif game_state == STATE_GAME_OVER:
        draw_game_over_screen(screen, SPRITES, font, score, draw_game)

    elif game_state == STATE_WIN:
        draw_win_screen(screen, SPRITES, font, score, draw_game)

pygame.quit()

serial_controller.close()

sys.exit()