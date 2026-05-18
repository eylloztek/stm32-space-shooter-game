# assets.py - Asset loading and management for the STM32 ADXL345 Space Shooter game

import os
import pygame

from settings import *


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")


def asset_path(*parts):
    return os.path.join(ASSET_DIR, *parts)


def load_sprite(path, size=None):
    image = pygame.image.load(path).convert_alpha()

    if size is not None:
        image = pygame.transform.scale(image, size)

    return image


def load_optional_sprite(path, size=None):
    if not os.path.exists(path):
        print("Missing asset:", path)
        return None

    return load_sprite(path, size)


def load_strip(path, frame_width, frame_height, scale=None):
    sheet = pygame.image.load(path).convert_alpha()

    sheet_width = sheet.get_width()
    frame_count = sheet_width // frame_width

    frames = []

    for i in range(frame_count):
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(
            sheet,
            (0, 0),
            (i * frame_width, 0, frame_width, frame_height)
        )

        if scale is not None:
            frame = pygame.transform.scale(frame, scale)

        frames.append(frame)

    return frames


def get_anim_frame(frames, speed_ms=100):
    if not frames:
        return None

    index = (pygame.time.get_ticks() // speed_ms) % len(frames)
    return frames[index]

def get_anim_frame_by_start_time(frames, start_time, speed_ms=100):
    if not frames:
        return None

    elapsed = pygame.time.get_ticks() - start_time
    index = (elapsed // speed_ms) % len(frames)

    return frames[index]

def get_sprite(sprite_or_frames, speed_ms=100):
    if isinstance(sprite_or_frames, list):
        return get_anim_frame(sprite_or_frames, speed_ms)

    return sprite_or_frames

def rotate_sprite(sprite, angle=180):
    return pygame.transform.rotate(sprite, angle)


def rotate_frames(frames, angle=180):
    return [pygame.transform.rotate(frame, angle) for frame in frames]

def trim_transparent_surface(surface):
    rect = surface.get_bounding_rect()

    if rect.width == 0 or rect.height == 0:
        return surface

    trimmed = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    trimmed.blit(surface, (0, 0), rect)

    return trimmed

def draw_pixel_progress_bar(
    screen,
    frame_sprite,
    x,
    y,
    ratio,
    fill_color,
    fill_offset_x=6,
    fill_offset_y=5,
    fill_width=None,
    fill_height=8
):
    ratio = max(0.0, min(1.0, ratio))

    frame_width = frame_sprite.get_width()

    if fill_width is None:
        fill_width = frame_width - (fill_offset_x * 2)

    visible_width = int(fill_width * ratio)

    # Fill
    if visible_width > 0:
        pygame.draw.rect(
            screen,
            fill_color,
            (
                x + fill_offset_x,
                y + fill_offset_y,
                visible_width,
                fill_height
            )
        )

        # Basic pixel-art highlight
        if fill_height >= 6:
            pygame.draw.line(
                screen,
                tuple(min(255, c + 45) for c in fill_color),
                (x + fill_offset_x, y + fill_offset_y),
                (x + fill_offset_x + visible_width - 1, y + fill_offset_y),
                1
            )

            pygame.draw.line(
                screen,
                tuple(max(0, c - 45) for c in fill_color),
                (x + fill_offset_x, y + fill_offset_y + fill_height - 1),
                (x + fill_offset_x + visible_width - 1, y + fill_offset_y + fill_height - 1),
                1
            )

    # frame is always drawn last to be on top
    screen.blit(frame_sprite, (x, y))

def draw_sprite_progress_bar(
    screen,
    frame_sprite,
    fill_sprite,
    x,
    y,
    ratio,
    fill_offset_x=4,
    fill_offset_y=4,
    fill_width=None,
    fill_height=None
):
    ratio = max(0.0, min(1.0, ratio))

    frame_width = frame_sprite.get_width()
    frame_height = frame_sprite.get_height()

    if fill_width is None:
        fill_width = frame_width - 8

    if fill_height is None:
        fill_height = frame_height - 8

    fill_width = max(1, fill_width)
    fill_height = max(1, fill_height)

    # Crop fill sprite to remove transparent edges for better scaling
    clean_fill = trim_transparent_surface(fill_sprite)

    if ratio > 0:
        visible_width = max(1, int(fill_width * ratio))

        scaled_fill = pygame.transform.scale(
            clean_fill,
            (fill_width, fill_height)
        )

        fill_part = scaled_fill.subsurface(
            (0, 0, visible_width, fill_height)
        )

        screen.blit(
            fill_part,
            (x + fill_offset_x, y + fill_offset_y)
        )

    # frame is always drawn last to be on top
    screen.blit(frame_sprite, (x, y))


def load_assets():
    return {
        # Background
        "background": load_optional_sprite(
            asset_path("background.png"),
            (WIDTH, HEIGHT)
        ),

        # Player
        "player_full": load_sprite(
            asset_path("player", "player_full.png"),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ),
        "player_slight_damage": load_sprite(
            asset_path("player", "player_slight_damage.png"),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ),
        "player_damaged": load_sprite(
            asset_path("player", "player_damaged.png"),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ),
        "player_very_damaged": load_sprite(
            asset_path("player", "player_very_damaged.png"),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ),
        "player_engine": load_sprite(
            asset_path("player", "player_engine.png"),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ),
        "player_engine_powering": load_strip(
            asset_path("player", "player_engine_powering.png"),
            frame_width=48,
            frame_height=48,
            scale=(PLAYER_WIDTH, PLAYER_HEIGHT)
        ),

        # Player shield
        "invincibility_shield": load_sprite(
            asset_path("invincibility_shield.png"),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        ),

        # Player bullet
        "player_bullet": load_strip(
            asset_path("player_bullet.png"),
            frame_width=PLAYER_BULLET_FRAME_WIDTH,
            frame_height=PLAYER_BULLET_FRAME_HEIGHT,
            scale=(PLAYER_BULLET_DRAW_WIDTH, PLAYER_BULLET_DRAW_HEIGHT)
        ),

        # Small enemy
        "small_enemy_base": rotate_sprite(
            load_sprite(
                asset_path("enemy", "small_enemy_base.png"),
                (ENEMY_WIDTH, ENEMY_HEIGHT)
            ),
            180
        ),
        "small_enemy_engine_frames": rotate_frames(
            load_strip(
                asset_path("enemy", "small_enemy_engine.png"),
                frame_width=64,
                frame_height=64,
                scale=(ENEMY_WIDTH, ENEMY_HEIGHT)
            ),
            180
        ),
        "small_enemy_bullet_frames": load_strip(
            asset_path("enemy", "small_enemy_bullet.png"),
            frame_width=SMALL_ENEMY_BULLET_FRAME_WIDTH,
            frame_height=SMALL_ENEMY_BULLET_FRAME_HEIGHT,
            scale=(SMALL_ENEMY_BULLET_DRAW_WIDTH, SMALL_ENEMY_BULLET_DRAW_HEIGHT)
        ),
        "small_enemy_destroyed_frames": load_strip(
            asset_path("enemy", "small_enemy_destroyed.png"),
            frame_width=64,
            frame_height=64,
            scale=(ENEMY_WIDTH, ENEMY_HEIGHT)
        ),

        # Big enemy / mini boss
        "big_enemy_base": rotate_sprite(
            load_sprite(
                asset_path("enemy", "big_enemy_base.png"),
                (MINI_BOSS_WIDTH, MINI_BOSS_HEIGHT)
            ),
            180
        ),
        "big_enemy_engine_frames": rotate_frames(
            load_strip(
                asset_path("enemy", "big_enemy_engine.png"),
                frame_width=128,
                frame_height=128,
                scale=(MINI_BOSS_WIDTH, MINI_BOSS_HEIGHT)
            ),
            180
        ),
        "big_enemy_bullet_frames": load_strip(
            asset_path("enemy", "big_enemy_bullet.png"),
            frame_width=BIG_ENEMY_BULLET_FRAME_WIDTH,
            frame_height=BIG_ENEMY_BULLET_FRAME_HEIGHT,
            scale=(BIG_ENEMY_BULLET_DRAW_WIDTH, BIG_ENEMY_BULLET_DRAW_HEIGHT)
        ),
        "big_enemy_destroyed_frames": load_strip(
            asset_path("enemy", "big_enemy_destroyed.png"),
            frame_width=128,
            frame_height=128,
            scale=(MINI_BOSS_WIDTH, MINI_BOSS_HEIGHT)
        ),

        # Power-ups
        "shield_powerup": load_strip(
            asset_path("powerups", "shield_powerup.png"),
            frame_width=32,
            frame_height=32,
            scale=(POWERUP_SIZE, POWERUP_SIZE)
        ),
        "rapid_fire_powerup": load_strip(
            asset_path("powerups", "rapid_fire_powerup.png"),
            frame_width=32,
            frame_height=32,
            scale=(POWERUP_SIZE, POWERUP_SIZE)
        ),
        "triple_shot_powerup": load_strip(
            asset_path("powerups", "triple_shot_powerup.png"),
            frame_width=32,
            frame_height=32,
            scale=(POWERUP_SIZE, POWERUP_SIZE)
        ),

        # UI
        "heart": load_sprite(
            asset_path("ui", "heart.png"),
            (28, 28)
        ),
        "bar_frame": load_sprite(
            asset_path("ui", "bar_frame.png"),
            (180, 18)
        ),
    }