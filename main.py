import sys
import os
from cybercases.game import CyberCasesGame

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    track1 = resource_path("assets/music/theme.mp3")
    track2 = resource_path("assets/music/case_music.mp3")
        
    CyberCasesGame().run()
