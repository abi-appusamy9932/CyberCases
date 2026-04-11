from __future__ import annotations
from dataclasses import dataclass, field
import pygame
import base64
import codecs
import sys

from cybercases.content import(
    CASES,
    FPS,
    GAME_SUBTITLE,
    GAME_TITLE,
    GLOBAL_TERMINAL_TIPS,
    MENU_INTRO,
    WINDOW_SIZE,
    CaseData
)

@dataclass
class TerminalState:
    history: list[str] = field(default_factory= list)
    current_input: str = ""
    cursor_index: int = 0
    current_step: int = 0
    wrong_answers: int = 0
    commands_used: int = 0
    command_history: list[str] = field(default_factory= list)
    history_index: int | None = None
    history_draft: str = ""

@dataclass
class CaseResult:
    case_number: int
    code_name: str
    title: str
    seconds_elapsed: int
    wrong_answers: int
    commands_used: int
    score: int

class CyberCasesGame:
    MIN_WINDOW_SIZE = (1100, 680)

    def __init__(self) -> None:
        pygame.init()
        pygame.key.set_repeat(350, 35)
        pygame.display.set_caption(GAME_TITLE)
        self.fullscreen = False
        self.windowed_size = WINDOW_SIZE
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = "menu"
        self.cases = CASES
        self.case_index = 0
        self.started = False
        self.active_case_completed = False
        self.case_started_ticks = 0
        self.results: list[CaseResult] = []
        self.last_result: CaseResult | None = None
        self.state = TerminalState()
        self.small_font = pygame.font.SysFont("consolas", 20)
        self.body_font = pygame.font.SysFont("consolas", 24)
        self.title_font = pygame.font.SysFont("consolas", 44, bold=True)
        self.hero_font = pygame.font.SysFont("consolas", 66, bold=True)
        self.metric_font = pygame.font.SysFont("consolas", 30, bold=True)
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.start_button = pygame.Rect(0, 0, 0, 0)
        self.command_bar = pygame.Rect(0, 0, 0, 0)

    @property
    def current_case(self) -> CaseData:
        return self.cases[self.case_index]
    
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            #finsh elif 

#need to add more functions

