# boss.py - Boss management for the STM32 ADXL345 Space Shooter game

import pygame

from settings import *
from game_state import STATE_WIN
from assets import get_anim_frame, draw_pixel_progress_bar


class BossManager:
    def __init__(self):
        self.active = False
        self.defeated = False
        self.boss = None

    def reset(self):
        self.active = False
        self.defeated = False
        self.boss = None

    def spawn(self, serial_controller):
        self.boss = {
            "x": WIDTH // 2 - MINI_BOSS_WIDTH // 2,
            "y": 40,
            "vx": BOSS_PHASE_1_SPEED,
            "hp": MINI_BOSS_HP,
            "max_hp": MINI_BOSS_HP,
            "phase": 1,
            "fire_delay": BOSS_PHASE_1_FIRE_DELAY, 
            "last_fire_time": pygame.time.get_ticks()
        }

        self.active = True
        serial_controller.send_command("BOSS")

    def update_phase(self, score, serial_controller):
        if score >= MINI_BOSS_SCORE and not self.active and not self.defeated:
            self.spawn(serial_controller)

    def update_phase_state(self, audio_manager=None):
        if not self.active or self.boss is None:
            return

        hp_ratio = self.boss["hp"] / self.boss["max_hp"]

        if hp_ratio <= BOSS_PHASE_2_HP_RATIO and self.boss["phase"] == 1:
            self.boss["phase"] = 2
            self.boss["fire_delay"] = BOSS_PHASE_2_FIRE_DELAY

        # Increase speed in phase 2
            if self.boss["vx"] >= 0:
                self.boss["vx"] = BOSS_PHASE_2_SPEED
            else:
                self.boss["vx"] = -BOSS_PHASE_2_SPEED
            if audio_manager is not None:
                audio_manager.play_boss_phase2()

    def update(self, audio_manager=None):
        if not self.active or self.boss is None:
            return

        self.update_phase_state(audio_manager)
        self.boss["x"] += self.boss["vx"]

        if self.boss["x"] <= 0:
            self.boss["x"] = 0
            self.boss["vx"] *= -1

        if self.boss["x"] >= WIDTH - MINI_BOSS_WIDTH:
            self.boss["x"] = WIDTH - MINI_BOSS_WIDTH
            self.boss["vx"] *= -1

    def get_hitbox(self):
        if self.boss is None:
            return None

        return pygame.Rect(
            int(self.boss["x"] + BOSS_HITBOX_OFFSET_X),
            int(self.boss["y"] + BOSS_HITBOX_OFFSET_Y),
            BOSS_HITBOX_WIDTH,
            BOSS_HITBOX_HEIGHT
        )

    def check_player_bullet_collision(
        self,
        bullet_manager,
        spawn_explosion_callback,
        serial_controller,
        audio_manager=None
    ):
        if not self.active or self.boss is None:
            return 0, None

        boss_rect = self.get_hitbox()
        score_gain = 0
        next_state = None

        for p_bullet in bullet_manager.player_bullets[:]:
            p_rect = pygame.Rect(
                p_bullet["x"],
                p_bullet["y"],
                PLAYER_BULLET_WIDTH,
                PLAYER_BULLET_HEIGHT
            )

            if p_rect.colliderect(boss_rect):
                if p_bullet in bullet_manager.player_bullets:
                    bullet_manager.player_bullets.remove(p_bullet)

                self.boss["hp"] -= 1

                if self.boss["hp"] <= 0:
                    spawn_explosion_callback(
                        self.boss["x"],
                        self.boss["y"],
                        "big"
                    )

                    if audio_manager is not None:
                        audio_manager.play_explosion()

                    self.active = False
                    self.defeated = True
                    self.boss = None

                    score_gain += 100
                    next_state = STATE_WIN

                    serial_controller.send_command("WIN")

                break

        return score_gain, next_state

    def draw(self, screen, sprites):
        if not self.active or self.boss is None:
            return

        x = int(self.boss["x"])
        y = int(self.boss["y"])

        engine_frame = get_anim_frame(
            sprites["big_enemy_engine_frames"],
            speed_ms=90
        )

        base_sprite = sprites["big_enemy_base"]

        if engine_frame is not None:
            engine_x = x + BIG_ENEMY_ENGINE_OFFSET_X
            engine_y = y + BIG_ENEMY_ENGINE_OFFSET_Y
            screen.blit(engine_frame, (engine_x, engine_y))

        screen.blit(base_sprite, (x, y))

        hp_ratio = self.boss["hp"] / self.boss["max_hp"]

        if self.boss["phase"] == 2:
            bar_color = BOSS_PHASE_2_HP_BAR_COLOR
        else:
            bar_color = BOSS_HP_BAR_COLOR

        draw_pixel_progress_bar(
            screen,
            sprites["bar_frame"],
            int(self.boss["x"] + MINI_BOSS_WIDTH // 2 - sprites["bar_frame"].get_width() // 2),
            int(self.boss["y"] - 26),
            hp_ratio,
            fill_color=bar_color,
            fill_offset_x=BOSS_BAR_FILL_OFFSET_X,
            fill_offset_y=BOSS_BAR_FILL_OFFSET_Y,
            fill_width=BOSS_BAR_FILL_WIDTH,
            fill_height=BOSS_BAR_FILL_HEIGHT
        )

        if SHOW_HITBOX:
            boss_hitbox = self.get_hitbox()
            if boss_hitbox is not None:
                pygame.draw.rect(screen, (255, 0, 0), boss_hitbox, 1)