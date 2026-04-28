from __future__ import annotations
from pathlib import Path
import pygame

class AudioManager:
    def __init__(self, music_dir: Path) -> None:
        self.music_dir = music_dir
        self.enabled = False
        self.current_music: str | None = None
        self.music_tracks = {
            "menu": self.music_dir / "theme.mp3",
            "case": self.music_dir / "case_music.mp3"
        }

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def match_scene(self, scene: str) -> None:
        if not self.enabled:
            return
        
        target_key = "case" if scene == "case" else "menu"
        target_path = self.music_tracks[target_key]
        if not target_path.exists():
            return
        
        target = str(target_path)
        if self.current_music == target:
            return
        
        pygame.mixer.music.load(target)
        pygame.mixer.music.set_volume(0.20 if scene == "case" else 0.18)
        pygame.mixer.music.play(-1, fade_ms=300)
        self.current_music = target
    