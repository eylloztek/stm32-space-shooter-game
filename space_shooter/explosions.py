# explosions.py - Manages explosion effects for the STM32 ADXL345 Space Shooter game

import pygame

from settings import *


class ExplosionManager:
    def __init__(self):
        self.explosions = []

    def reset(self):
        self.explosions.clear()

    def spawn_explosion(self, x, y, explosion_type):
        self.explosions.append({
            "x": x,
            "y": y,
            "type": explosion_type,
            "start_time": pygame.time.get_ticks()
        })

    def update(self, sprites):
        current_time = pygame.time.get_ticks()

        for explosion in self.explosions[:]:
            if explosion["type"] == "big":
                frames = sprites["big_enemy_destroyed_frames"]
            else:
                frames = sprites["small_enemy_destroyed_frames"]

            duration = len(frames) * EXPLOSION_FRAME_TIME

            if current_time - explosion["start_time"] > duration:
                self.explosions.remove(explosion)

    def draw(self, screen, sprites):
        current_time = pygame.time.get_ticks()

        for explosion in self.explosions:
            if explosion["type"] == "big":
                frames = sprites["big_enemy_destroyed_frames"]
            else:
                frames = sprites["small_enemy_destroyed_frames"]

            elapsed = current_time - explosion["start_time"]
            frame_index = min(
                len(frames) - 1,
                elapsed // EXPLOSION_FRAME_TIME
            )

            sprite = frames[frame_index]
            screen.blit(
                sprite,
                (int(explosion["x"]), int(explosion["y"]))
            )