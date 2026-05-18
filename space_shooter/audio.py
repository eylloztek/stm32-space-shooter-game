# audio.py - Audio management for the STM32 ADXL345 Space Shooter game

import pygame

from settings import *
from assets import asset_path


class AudioManager:
    def __init__(self):
        self.current_music = None

        self.music_paths = {
            "main": asset_path("audio", "main_theme.ogg"),
            "boss": asset_path("audio", "boss_theme.ogg"),
            "victory": asset_path("audio", "victory.ogg"),
            "defeat": asset_path("audio", "defeat.ogg"),
        }

        self.sfx = {
            "player_fire": self.load_sound(
                asset_path("audio", "player_fire.wav"),
                SFX_PLAYER_FIRE_VOLUME
            ),
            "explosion": self.load_sound(
                asset_path("audio", "explosion.wav"),
                SFX_EXPLOSION_VOLUME
            ),
            "powerup": self.load_sound(
                asset_path("audio", "powerup.wav"),
                SFX_POWERUP_VOLUME
            ),
            "player_hit": self.load_sound(
                asset_path("audio", "player_hit.wav"),
            SFX_PLAYER_HIT_VOLUME
            ),
            "boss_phase2": self.load_sound(
                asset_path("audio", "boss_phase2.wav"),
                SFX_BOSS_PHASE2_VOLUME
            ),
        }
        

    def load_sound(self, path, volume):
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(volume)
            return sound
        except pygame.error as e:
            print("Sound load error:", path, e)
            return None

    def play_music(self, music_name, volume, loop=True):
        if self.current_music == music_name:
            pygame.mixer.music.set_volume(volume)
            return

        try:
            pygame.mixer.music.load(self.music_paths[music_name])
            pygame.mixer.music.set_volume(volume)

            loops = -1 if loop else 0
            pygame.mixer.music.play(loops)

            self.current_music = music_name

        except pygame.error as e:
            print("Music load/play error:", music_name, e)

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None

    def update_music(self, game_state, boss_active):
        """
        Music rules:
        - START: main theme, louder
        - PLAYING/PAUSED before boss: main theme, lower
        - Boss active: boss theme, loop
        - WIN: victory, once
        - GAME_OVER: defeat, once
        """

        if game_state == "START":
            self.play_music(
                "main",
                MUSIC_MAIN_MENU_VOLUME,
                loop=True
            )

        elif game_state == "PLAYING":
            if boss_active:
                self.play_music(
                    "boss",
                    MUSIC_BOSS_VOLUME,
                    loop=True
                )
            else:
                self.play_music(
                    "main",
                    MUSIC_GAME_VOLUME,
                    loop=True
                )

        elif game_state == "PAUSED":
            if boss_active:
                self.play_music(
                    "boss",
                    MUSIC_BOSS_VOLUME,
                    loop=True
                )
            else:
                self.play_music(
                    "main",
                    MUSIC_GAME_VOLUME,
                    loop=True
                )

        elif game_state == "WIN":
            self.play_music(
                "victory",
                MUSIC_VICTORY_VOLUME,
                loop=False
            )

        elif game_state == "GAME_OVER":
            self.play_music(
                "defeat",
                MUSIC_DEFEAT_VOLUME,
                loop=False
            )

    def play_sfx(self, name):
        sound = self.sfx.get(name)

        if sound is not None:
            sound.play()

    def play_player_fire(self):
        self.play_sfx("player_fire")

    def play_explosion(self):
        self.play_sfx("explosion")

    def play_powerup(self):
        self.play_sfx("powerup")

    def play_player_hit(self):
        self.play_sfx("player_hit")

    def play_boss_phase2(self):
        self.play_sfx("boss_phase2")

    def reset_state(self):
        self.current_music = None