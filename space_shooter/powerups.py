# powerups.py - Power-up management for the STM32 ADXL345 Space Shooter game

import pygame
import random

from settings import *
from assets import get_sprite, draw_pixel_progress_bar


class PowerupManager:
    def __init__(self):
        self.powerups = []

        self.rapid_fire_active = False
        self.rapid_fire_start_time = 0

        self.triple_shot_active = False
        self.triple_shot_start_time = 0

    def reset(self):
        self.powerups.clear()

        self.rapid_fire_active = False
        self.rapid_fire_start_time = 0

        self.triple_shot_active = False
        self.triple_shot_start_time = 0

    def spawn_powerup(self, x, y):
        powerup_type = random.choice([
            "shield",
            "rapid_fire",
            "triple_shot"
        ])

        self.powerups.append({
            "x": x,
            "y": y,
            "type": powerup_type
        })

    def update_powerups(self):
        for powerup in self.powerups[:]:
            powerup["y"] += POWERUP_SPEED

            if powerup["y"] > HEIGHT:
                self.powerups.remove(powerup)

    def update_rapid_fire(self):
        if self.rapid_fire_active:
            current_time = pygame.time.get_ticks()

            if current_time - self.rapid_fire_start_time > RAPID_FIRE_DURATION:
                self.rapid_fire_active = False

    def update_triple_shot(self):
        if self.triple_shot_active:
            current_time = pygame.time.get_ticks()

            if current_time - self.triple_shot_start_time > TRIPLE_SHOT_DURATION:
                self.triple_shot_active = False

    def update(self):
        self.update_powerups()
        self.update_rapid_fire()
        self.update_triple_shot()

    def check_collision(self, player, audio_manager=None):
        score_gain = 0

        player_rect = player.get_sprite_rect()

        for powerup in self.powerups[:]:
            powerup_rect = pygame.Rect(
                powerup["x"],
                powerup["y"],
                POWERUP_SIZE,
                POWERUP_SIZE
            )

            if player_rect.colliderect(powerup_rect):

                # Apply power-up effect
                if powerup["type"] == "shield":
                    if player.shield_active:
                        score_gain += 20
                    else:
                        player.shield_active = True

                elif powerup["type"] == "rapid_fire":
                    self.rapid_fire_active = True
                    self.rapid_fire_start_time = pygame.time.get_ticks()

                elif powerup["type"] == "triple_shot":
                    self.triple_shot_active = True
                    self.triple_shot_start_time = pygame.time.get_ticks()
                    
                if audio_manager is not None:
                    audio_manager.play_powerup()

                self.powerups.remove(powerup)

        return score_gain

    def draw_powerups(self, screen, sprites):
        for powerup in self.powerups:
            if powerup["type"] == "shield":
                sprite = get_sprite(
                    sprites["shield_powerup"],
                    speed_ms=120
                )

            elif powerup["type"] == "rapid_fire":
                sprite = get_sprite(
                    sprites["rapid_fire_powerup"],
                    speed_ms=120
                )

            elif powerup["type"] == "triple_shot":
                sprite = get_sprite(
                    sprites["triple_shot_powerup"],
                    speed_ms=120
                )

            else:
                sprite = get_sprite(
                    sprites["shield_powerup"],
                    speed_ms=120
                )

            if sprite is not None:
                screen.blit(
                    sprite,
                    (int(powerup["x"]), int(powerup["y"]))
                )

    def draw_powerup_bar(self, screen, sprites, font, label, icon_sprite, x, y, remaining_ratio, fill_color):
        label_text = font.render(label, True, (255, 255, 255))
        screen.blit(label_text, (x, y - 18))

        icon = get_sprite(icon_sprite, speed_ms=120)

        if icon is not None:
            screen.blit(icon, (x, y + 2))

        draw_pixel_progress_bar(
            screen,
            sprites["bar_frame"],
            x + 38,
            y + 6,
            remaining_ratio,
            fill_color=fill_color,
            fill_offset_x=POWERUP_BAR_FILL_OFFSET_X,
            fill_offset_y=POWERUP_BAR_FILL_OFFSET_Y,
            fill_width=POWERUP_BAR_FILL_WIDTH,
            fill_height=POWERUP_BAR_FILL_HEIGHT
        )

    def draw_powerup_bars(self, screen, sprites, font):
        current_time = pygame.time.get_ticks()

        bar_x = WIDTH - 240
        bar_y = 30

        if self.rapid_fire_active:
            elapsed = current_time - self.rapid_fire_start_time
            remaining_ms = max(0, RAPID_FIRE_DURATION - elapsed)
            remaining_ratio = remaining_ms / RAPID_FIRE_DURATION
            remaining_sec = remaining_ms // 1000 + 1

            self.draw_powerup_bar(
                screen,
                sprites,
                font,
                f"Rapid {remaining_sec}s",
                sprites["rapid_fire_powerup"],
                bar_x,
                bar_y,
                remaining_ratio,
                POWERUP_RAPID_BAR_COLOR
            )

            bar_y += 55

        if self.triple_shot_active:
            elapsed = current_time - self.triple_shot_start_time
            remaining_ms = max(0, TRIPLE_SHOT_DURATION - elapsed)
            remaining_ratio = remaining_ms / TRIPLE_SHOT_DURATION
            remaining_sec = remaining_ms // 1000 + 1

            self.draw_powerup_bar(
                screen,
                sprites,
                font,
                f"Triple {remaining_sec}s",
                sprites["triple_shot_powerup"],
                bar_x,
                bar_y,
                remaining_ratio,
                POWERUP_TRIPLE_BAR_COLOR
            )