# enemy.py - Enemy management for the STM32 ADXL345 Space Shooter game

import pygame
import random

from settings import *
from assets import get_anim_frame


class EnemyManager:
    def __init__(self):
        self.enemies = []

    def reset(self):
        self.enemies.clear()

    def spawn_enemy(self, difficulty_level):
        x = random.randint(0, WIDTH - ENEMY_WIDTH)

        self.enemies.append({
            "x": x,
            "y": -ENEMY_HEIGHT,
            "type": "small",
            "width": ENEMY_WIDTH,
            "height": ENEMY_HEIGHT,
            "speed": random.randint(
                2,
                min(MAX_ENEMY_SPEED, 3 + difficulty_level)
            ),
            "last_fire_time": pygame.time.get_ticks()
        })

    def update_enemies(
        self,
        player,
        serial_controller,
        set_game_over_callback,
        audio_manager=None
    ):
        player_rect = player.get_hitbox()

        for enemy in self.enemies[:]:

            enemy["y"] += enemy["speed"]

            enemy_rect = self.get_enemy_hitbox(enemy)

            if enemy_rect.colliderect(player_rect):
                damage_result = player.take_damage()

                if damage_result in ["HIT", "SHIELD_HIT"]:
                    serial_controller.send_command("HIT")
                    if audio_manager is not None:
                        audio_manager.play_player_hit()

                elif damage_result == "DEAD":
                    set_game_over_callback()
                    serial_controller.send_command("GAME_OVER")
                    if audio_manager is not None:
                        audio_manager.play_player_hit()

                if enemy in self.enemies:
                    self.enemies.remove(enemy)

            if enemy["y"] > HEIGHT:
                self.enemies.remove(enemy)

    def draw_enemies(self, screen, sprites):
        for enemy in self.enemies:
            x = int(enemy["x"])
            y = int(enemy["y"])

            if enemy.get("type") == "small":
                engine_frame = get_anim_frame(
                    sprites["small_enemy_engine_frames"],
                    speed_ms=90
                )

                base_sprite = sprites["small_enemy_base"]

                if engine_frame is not None:
                    engine_x = x + SMALL_ENEMY_ENGINE_OFFSET_X
                    engine_y = y + SMALL_ENEMY_ENGINE_OFFSET_Y

                    # Engine drawn first for better layering.
                    screen.blit(engine_frame, (engine_x, engine_y))

                # Base drawn after engine for better layering.
                screen.blit(base_sprite, (x, y))

                if SHOW_HITBOX:
                    pygame.draw.rect(
                        screen,
                        (255, 0, 0),
                        self.get_enemy_hitbox(enemy),
                        1
                    )

    def get_enemy_hitbox(self, enemy):
        return pygame.Rect(
            int(enemy["x"] + ENEMY_HITBOX_OFFSET_X),
            int(enemy["y"] + ENEMY_HITBOX_OFFSET_Y),
            ENEMY_HITBOX_WIDTH,
            ENEMY_HITBOX_HEIGHT
    )

    def check_player_bullet_collision(
        self,
        bullet_manager,
        spawn_explosion_callback,
        spawn_powerup_callback,
        audio_manager=None
    ):
        score_gain = 0

        for p_bullet in bullet_manager.player_bullets[:]:
            p_rect = pygame.Rect(
                p_bullet["x"],
                p_bullet["y"],
                PLAYER_BULLET_WIDTH,
                PLAYER_BULLET_HEIGHT
            )

            for enemy in self.enemies[:]:
                enemy_rect = self.get_enemy_hitbox(enemy)

                if p_rect.colliderect(enemy_rect):
                    if p_bullet in bullet_manager.player_bullets:
                        bullet_manager.player_bullets.remove(p_bullet)

                    if enemy in self.enemies:
                        enemy_center_x = enemy["x"] + enemy["width"] // 2 - POWERUP_SIZE // 2
                        enemy_center_y = enemy["y"] + enemy["height"] // 2

                        spawn_explosion_callback(
                            enemy["x"],
                            enemy["y"],
                            "small"
                        )
                        if audio_manager is not None:
                            audio_manager.play_explosion()

                        self.enemies.remove(enemy)

                        if random.random() < POWERUP_DROP_CHANCE:
                            spawn_powerup_callback(
                                enemy_center_x,
                                enemy_center_y
                            )

                    score_gain += 10
                    break

        return score_gain