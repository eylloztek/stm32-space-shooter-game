# player.py - Player management for the STM32 ADXL345 Space Shooter game

import pygame

from settings import *
from assets import get_sprite


class Player:
    def __init__(self):
        self.x = WIDTH // 2 - PLAYER_WIDTH // 2
        self.y = HEIGHT - 120

        self.lives = MAX_LIVES
        self.shield_active = False

        self.invincible = False
        self.invincible_start_time = 0

    def reset(self):
        self.x = WIDTH // 2 - PLAYER_WIDTH // 2
        self.y = HEIGHT - 120

        self.lives = MAX_LIVES
        self.shield_active = False

        self.invincible = False
        self.invincible_start_time = 0

    def apply_dead_zone(self, value):
        if abs(value) < DEAD_ZONE:
            return 0
        return value

    def convert_adxl_to_speed(self, value):
        value = self.apply_dead_zone(value)

        if value == 0:
            return 0

        direction = 1 if value > 0 else -1
        magnitude = abs(value)

        return direction * (2 + magnitude * 0.08)

    def update_movement(self, accel_x, accel_y):
        vx = self.convert_adxl_to_speed(accel_x)
        vy = self.convert_adxl_to_speed(accel_y)

        self.x += vx
        self.y += -vy

        self.x = max(0, min(WIDTH - PLAYER_WIDTH, self.x))

        min_y = HEIGHT // 2
        max_y = HEIGHT - PLAYER_HEIGHT
        self.y = max(min_y, min(max_y, self.y))

    def update_invincibility(self):
        if self.invincible:
            current_time = pygame.time.get_ticks()

            if current_time - self.invincible_start_time > INVINCIBLE_DURATION:
                self.invincible = False

    def take_damage(self):
        if self.invincible:
            return "NO_DAMAGE"

        if self.shield_active:
            self.shield_active = False
            self.invincible = True
            self.invincible_start_time = pygame.time.get_ticks()
            return "SHIELD_HIT"

        self.lives -= 1
        self.invincible = True
        self.invincible_start_time = pygame.time.get_ticks()

        if self.lives <= 0:
            return "DEAD"

        return "HIT"

    def get_hitbox(self):
        return pygame.Rect(
            int(self.x + PLAYER_HITBOX_OFFSET_X),
            int(self.y + PLAYER_HITBOX_OFFSET_Y),
            PLAYER_HITBOX_WIDTH,
            PLAYER_HITBOX_HEIGHT
        )

    def get_sprite_rect(self):
        return pygame.Rect(
            int(self.x),
            int(self.y),
            PLAYER_WIDTH,
            PLAYER_HEIGHT
        )
    
    

    def get_player_hitbox(self):
        return pygame.Rect(
            int(self.x + PLAYER_HITBOX_OFFSET_X),
            int(self.y + PLAYER_HITBOX_OFFSET_Y),
            PLAYER_HITBOX_WIDTH,
            PLAYER_HITBOX_HEIGHT
    )



    def get_base_sprite(self, sprites):
        if self.lives >= 4:
            return sprites["player_full"]
        elif self.lives == 3:
            return sprites["player_slight_damage"]
        elif self.lives == 2:
            return sprites["player_damaged"]
        else:
            return sprites["player_very_damaged"]

    def draw(self, screen, sprites):
        if self.invincible:
            blink = (pygame.time.get_ticks() // 150) % 2
            if blink == 0:
                return

        x = int(self.x)
        y = int(self.y)

        # 1) Powering engine animation - underneath the base sprite, can be drawn first
        powering_engine = get_sprite(
            sprites["player_engine_powering"],
            speed_ms=90
        )

        if powering_engine is not None:
            powering_x = x + PLAYER_POWERING_ENGINE_OFFSET_X
            powering_y = y + PLAYER_POWERING_ENGINE_OFFSET_Y
            screen.blit(powering_engine, (powering_x, powering_y))

        # 2) Base engine layer - underneath the base sprite, can be drawn before powering engine
        engine_sprite = sprites["player_engine"]

        if engine_sprite is not None:
            engine_x = x + PLAYER_ENGINE_OFFSET_X
            engine_y = y + PLAYER_ENGINE_OFFSET_Y
            screen.blit(engine_sprite, (engine_x, engine_y))

        # 3) Player base 
        screen.blit(self.get_base_sprite(sprites), (x, y))

        # 4) Shield overlay
        if self.shield_active:
            shield_sprite = sprites["invincibility_shield"]
            shield_x = int(self.x + PLAYER_WIDTH // 2 - shield_sprite.get_width() // 2)
            shield_y = int(self.y + PLAYER_HEIGHT // 2 - shield_sprite.get_height() // 2)
            screen.blit(shield_sprite, (shield_x, shield_y))

        if SHOW_HITBOX:
            pygame.draw.rect(screen, (255, 0, 0), self.get_hitbox(), 1)