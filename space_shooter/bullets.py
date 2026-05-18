# bullets.py - Bullet management for the STM32 ADXL345 Space Shooter game

import pygame

from settings import *
from assets import get_sprite, get_anim_frame, get_anim_frame_by_start_time


class BulletManager:
    def __init__(self):
        self.player_bullets = []
        self.enemy_bullets = []

        self.last_rapid_fire_time = 0

    def reset(self):
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.last_rapid_fire_time = 0

    # =========================
    # PLAYER BULLETS
    # =========================

    def shoot_player_bullet(self, player, triple_shot_active, serial_controller, audio_manager=None):
        current_time = pygame.time.get_ticks()
        center_x = player.x + PLAYER_WIDTH // 2 - PLAYER_BULLET_WIDTH // 2
        bullet_y = player.y

        if triple_shot_active:
            self.player_bullets.append({
                "x": center_x,
                "y": bullet_y,
                "vx": 0,
                "vy": -PLAYER_BULLET_SPEED,
                "spawn_time": current_time
            })

            self.player_bullets.append({
                "x": center_x,
                "y": bullet_y,
                "vx": -TRIPLE_SHOT_SIDE_SPEED,
                "vy": -PLAYER_BULLET_SPEED,
                "spawn_time": current_time
            })

            self.player_bullets.append({
                "x": center_x,
                "y": bullet_y,
                "vx": TRIPLE_SHOT_SIDE_SPEED,
                "vy": -PLAYER_BULLET_SPEED,
                "spawn_time": current_time
            })

        else:
            self.player_bullets.append({
                "x": center_x,
                "y": bullet_y,
                "vx": 0,
                "vy": -PLAYER_BULLET_SPEED,
                "spawn_time": current_time
            })

        serial_controller.send_command("FIRE")
        if audio_manager is not None:
            audio_manager.play_player_fire()

    def handle_fire_input(
        self,
        player,
        serial_controller,
        rapid_fire_active,
        triple_shot_active,
        audio_manager=None
    ):
        current_time = pygame.time.get_ticks()

        if rapid_fire_active:
            if serial_controller.fire_hold == 1:
                if current_time - self.last_rapid_fire_time > RAPID_FIRE_COOLDOWN:
                    self.shoot_player_bullet(
                        player,
                        triple_shot_active,
                        serial_controller,
                        audio_manager
                    )
                    self.last_rapid_fire_time = current_time
        else:
            if serial_controller.fire_pressed == 1:
                self.shoot_player_bullet(
                    player,
                    triple_shot_active,
                    serial_controller,
                    audio_manager
                )

    def update_player_bullets(self):
        for bullet in self.player_bullets[:]:
            bullet["x"] += bullet.get("vx", 0)
            bullet["y"] += bullet.get("vy", -PLAYER_BULLET_SPEED)

            if (
                bullet["y"] < -PLAYER_BULLET_HEIGHT
                or bullet["x"] < -PLAYER_BULLET_WIDTH
                or bullet["x"] > WIDTH + PLAYER_BULLET_WIDTH
            ):
                self.player_bullets.remove(bullet)

    def draw_player_bullets(self, screen, sprites):
        frames = sprites["player_bullet"]

        for bullet in self.player_bullets:
            sprite = get_anim_frame_by_start_time(
                frames,
                bullet.get("spawn_time", pygame.time.get_ticks()),
                speed_ms=BULLET_ANIMATION_SPEED_MS
            )

            if sprite is not None:
                draw_x = int(
                    bullet["x"] + PLAYER_BULLET_WIDTH // 2 - sprite.get_width() // 2
                )
                draw_y = int(
                    bullet["y"] + PLAYER_BULLET_HEIGHT // 2 - sprite.get_height() // 2
                )

                screen.blit(sprite, (draw_x, draw_y))

    # =========================
    # ENEMY BULLETS
    # =========================

    def enemy_fire(self, enemies, enemy_bullet_speed):
        current_time = pygame.time.get_ticks()

        for enemy in enemies:
            if current_time - enemy["last_fire_time"] > ENEMY_FIRE_DELAY:
                bullet_x = enemy["x"] + enemy["width"] // 2 - ENEMY_BULLET_WIDTH // 2
                bullet_y = enemy["y"] + enemy["height"]

                self.enemy_bullets.append({
                    "x": bullet_x,
                    "y": bullet_y,
                    "type": "small",
                    "width": ENEMY_BULLET_WIDTH,
                    "height": ENEMY_BULLET_HEIGHT,
                    "speed": enemy_bullet_speed,
                    "spawn_time": current_time
                })

                enemy["last_fire_time"] = current_time

    def mini_boss_fire(self, mini_boss, mini_boss_active, enemy_bullet_speed):
        if not mini_boss_active or mini_boss is None:
            return

        current_time = pygame.time.get_ticks()
        fire_delay = mini_boss.get("fire_delay", BOSS_PHASE_1_FIRE_DELAY)

        if current_time - mini_boss["last_fire_time"] <= fire_delay:
            return
        
        center_x = mini_boss["x"] + MINI_BOSS_WIDTH // 2 - BIG_ENEMY_BULLET_WIDTH // 2
        bullet_y = mini_boss["y"] + MINI_BOSS_HEIGHT

        phase = mini_boss.get("phase", 1)

        if phase == 1:
            self.enemy_bullets.append({
                "x": center_x,
                "y": bullet_y,
                "vx": 0,
                "type": "big",
                "width": BIG_ENEMY_BULLET_WIDTH,
                "height": BIG_ENEMY_BULLET_HEIGHT,
                "speed": enemy_bullet_speed + 1,
                "spawn_time": current_time
            })
        else:
            self.enemy_bullets.append({
                "x": center_x,
                "y": bullet_y,
                "vx": 0,
                "type": "big",
                "width": BIG_ENEMY_BULLET_WIDTH,
                "height": BIG_ENEMY_BULLET_HEIGHT,
                "speed": enemy_bullet_speed + 2,
                "spawn_time": current_time
            })

            self.enemy_bullets.append({
            "x": center_x,
            "y": bullet_y,
            "vx": -BOSS_PHASE_2_SPREAD_SPEED,
            "type": "big",
            "width": BIG_ENEMY_BULLET_WIDTH,
            "height": BIG_ENEMY_BULLET_HEIGHT,
            "speed": enemy_bullet_speed + 2,
            "spawn_time": current_time
            })

            self.enemy_bullets.append({
                "x": center_x,
                "y": bullet_y,
                "vx": BOSS_PHASE_2_SPREAD_SPEED,
                "type": "big",
                "width": BIG_ENEMY_BULLET_WIDTH,
                "height": BIG_ENEMY_BULLET_HEIGHT,
                "speed": enemy_bullet_speed + 2,
                "spawn_time": current_time
            })

        mini_boss["last_fire_time"] = current_time

    def update_enemy_bullets(self):
        for bullet in self.enemy_bullets[:]:
            bullet["x"] += bullet.get("vx", 0)
            bullet["y"] += bullet.get("speed", ENEMY_BULLET_SPEED)

            if (
                bullet["y"] > HEIGHT
                or bullet["x"] < -BIG_ENEMY_BULLET_WIDTH
                or bullet["x"] > WIDTH + BIG_ENEMY_BULLET_WIDTH
            ):
                self.enemy_bullets.remove(bullet)

    def draw_enemy_bullets(self, screen, sprites):
        for bullet in self.enemy_bullets:
            if bullet.get("type") == "big":
                frames = sprites["big_enemy_bullet_frames"]
            else:
                frames = sprites["small_enemy_bullet_frames"]

            sprite = get_anim_frame_by_start_time(
                frames,
                bullet.get("spawn_time", pygame.time.get_ticks()),
                speed_ms=BULLET_ANIMATION_SPEED_MS
            )

            if sprite is not None:
                bullet_width = bullet.get("width", ENEMY_BULLET_WIDTH)
                bullet_height = bullet.get("height", ENEMY_BULLET_HEIGHT)

                draw_x = int(
                    bullet["x"] + bullet_width // 2 - sprite.get_width() // 2
                )
                draw_y = int(
                    bullet["y"] + bullet_height // 2 - sprite.get_height() // 2
                )

                screen.blit(sprite, (draw_x, draw_y))

    def check_enemy_bullet_collision(self, player, serial_controller, set_game_over_callback, audio_manager=None):
        player_rect = player.get_hitbox()

        for bullet in self.enemy_bullets[:]:
            bullet_rect = pygame.Rect(
                bullet["x"],
                bullet["y"],
                bullet.get("width", ENEMY_BULLET_WIDTH),
                bullet.get("height", ENEMY_BULLET_HEIGHT)
            )

            if player_rect.colliderect(bullet_rect):
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

                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)