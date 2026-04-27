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
        self.scroll_offsets: dict[str, int] = {}
        self.scroll_regions: dict[str, dict[str, object]] = {}

    @property
    def current_case(self) -> CaseData:
        return self.cases[self.case_index]
    
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                width = max(self.MIN_WINDOW_SIZE[0], event.w)
                height = max(self.MIN_WINDOW_SIZE[1], event.h)
                self.windowed_size = (width, height)
                self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            elif event.type == pygame.MOUSEWHEEL:
                self.handle_mousewheel(event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
    
    def handle_click(self, position: tuple[int, int]) -> None:
        if self.scene == "menu" and self.start_button.collidepoint(position):
            self.launch_from_menu()

    def handle_keydown(self, event: pygame.event.Event) -> None:
        if self.scene == "menu":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.launch_from_menu()
            return
        
        if self.scene == "case_complete":
            if event.key in (pygame.K_RETURN, pygame.K_n):
                self.next_case()
            elif event.key == pygame.K_r:
                self.reset_case()
            elif event.key == pygame.K_ESCAPE:
                self.scene = "menu"
            return
        
        if self.scene == "game_complete":
            if event.key in (pygame.K_RETURN, pygame.K_r):
                self.start_game()
            elif event.key == pygame.K_ESCAPE:
                self.scene = "menu"
            return
        
        if event.key == pygame.K_RETURN:
            command = self.state.current_input.strip()
            self.clear_input()
            if command:
                self.execute_command(command)
        elif event.key == pygame.K_BACKSPACE:
            self.delete_backward()
        elif event.key == pygame.K_DELETE:
            self.delete_forward()
        elif event.key == pygame.K_LEFT:
            self.move_cursor(-1)
        elif event.key == pygame.K_RIGHT:
            self.move_cursor(1)
        elif event.key == pygame.K_HOME:
            self.state.cursor_index = 0
        elif event.key == pygame.K_END:
            self.state.cursor_index = len(self.state.current_input)
        elif event.key == pygame.K_UP:
            self.browse_history(-1)
        elif event.key == pygame.K_DOWN:
            self.browse_history(1)
        elif event.key == pygame.K_ESCAPE:
            self.scene = "menu"
        elif event.unicode and event.unicode.isprintable() and not event.mod & (pygame.KMOD_CTRL | pygame.KMOD_ALT | pygame.KMOD_META):
            self.insert_text(event.unicode)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)

    def update(self, dt: float) -> None:
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible

    def draw(self) -> None:
        self.screen.fill((7,12,18))
        self.scroll_regions = {}
        self.draw_grid()
        if self.scene == "menu":
            self.draw_menu()
        elif self.scene == "case":
            self.draw_case()
        elif self.scene == "case_complete":
            self.draw_case_complete()
        else:
            self.draw_game_complete()
        pygame.display.flip()

    def draw_grid(self) -> None:
        width, height = self.screen.get_size()
        for x in range(0, width, 32):
            pygame.draw.line(self.screen, (16, 28, 38), (x, 0), (x, height), 1)
        for y in range(0, height, 32):
            pygame.draw.line(self.screen, (12, 22, 30), (0,y), (width, y), 1)

    def handle_mousewheel(self, amount:int) -> None:
        mouse_position = pygame.mouse.get_pos()
        for region_id, region in self.scroll_regions.items():
            viewport = region["viewport"]
            max_offset = region["max_offset"]
            if not isinstance(viewport, pygame.Rect) or not isinstance(max_offset, int):
                continue
            if viewport.collidepoint(mouse_position):
                current_offset = self.scroll_offsets.get(region_id, 0)
                self.scroll_offsets[region_id] = max(0, min(max_offset, current_offset - amount*32))
                return
            
    def draw_menu(self) -> None:
        width, height = self.screen.get_size()
        panel = pygame.Rect(48, 48, width - 96, height - 96)
        self.draw_panel(panel, "Mission Control")
        title = self.hero_font.render(GAME_TITLE, True, (91, 241, 196))
        self.screen.blit(title, (panel.x + 24, panel.y + 30))

        subtitle_rect = pygame.Rect(panel.x + 26, panel.y + 116, panel.width - 52, 46)
        self.draw_wrapped_text([GAME_SUBTITLE], subtitle_rect, self.body_font, (185, 229, 217))

        intro_rect = pygame.Rect(panel.x+26, panel.y+178, panel.width-52, 110)
        self.draw_wrapped_text(list(MENU_INTRO), intro_rect, self.small_font, (205, 229, 226))

        cards_y = panel.y +298
        cards_width = panel.width -52
        gap = 16
        card_width = (cards_width - gap *2) // 3
        card_height = 176
        for index, case in enumerate(self.cases):
            rect = pygame.Rect(panel.x+26+index * (card_width + gap), cards_y, card_width, card_height)
            self.draw_case_card(rect, case, self.get_case_status(index))
        
        self.start_button = pygame.Rect(panel.x + 24, panel.bottom -86, 280, 58)
        pygame.draw.rect(self.screen, (18, 44, 41), self.start_button, border_radius=12)
        pygame.draw.rect(self.screen, (91, 241, 196), self.start_button, width=2, border_radius=12)
        label = self.body_font.render(self.get_menu_action_label(), True, (234, 255, 250))
        self.screen.blit(label, (self.start_button.x + 22, self.start_button.y + 14))

        hint_rect = pygame.Rect(
            self.start_button.right + 28, 
            self.start_button.y + 2, 
            panel.right - self.start_button.right - 54, 
            64)
        hint_lines = [
            f"Game Progress: {len(self.results)} / {len(self.cases)} cases cleared.",
            "Press Enter or click the button."
        ]

        self.draw_wrapped_text(hint_lines, hint_rect, self.small_font, (125, 173, 164))
        

    def draw_case(self) -> None:
        width, height = self.screen.get_size()
        margin = 36
        gutter = 18
        left_width = max(330, int(width * 0.30))
        right_width = width - (margin * 2) - gutter - left_width
        top_height = max(220, int(height * 0.30))
        middle_height = max(170, int(height * 0.20))
        bottom_height = height - (margin * 2) - gutter * 2 - top_height - middle_height

        case_rect = pygame.Rect(margin, margin, left_width, top_height)
        objectives_rect = pygame.Rect(margin, case_rect.bottom + gutter, left_width, middle_height)
        hints_rect = pygame.Rect(margin, objectives_rect.bottom + gutter, left_width, bottom_height)
        terminal_rect = pygame.Rect(case_rect.right + gutter, margin, right_width, height - margin * 2)

        self.draw_panel(case_rect, "Case File")
        self.draw_panel(objectives_rect, "Objectives")
        self.draw_panel(hints_rect, "Hints")
        self.draw_panel(terminal_rect, "Responder Terminal")

        story_lines = [self.current_case.code_name, "", *self.current_case.story_lines]
        self.draw_scrollable_text(
            "case_story",
            story_lines,
            pygame.Rect(case_rect.x + 20, case_rect.y + 42, case_rect.width - 40, case_rect.height - 62),
            self.small_font,
            (212, 237, 232),
            accent_first_line=True,
        )

        step = self.current_case.puzzle_steps[self.state.current_step]
        objective_lines = [
            "Current objective:",
            step.prompt,
            "",
            f"Progress: {self.state.current_step +1} / {len(self.current_case.puzzle_steps)}",
        ]
        self.draw_scrollable_text(
            "case_objectives",
            objective_lines,
            pygame.Rect(objectives_rect.x + 20, objectives_rect.y + 42, objectives_rect.width - 40, objectives_rect.height - 96),
            self.small_font,
            (230, 255, 250),
        )

        progress_bar = pygame.Rect(objectives_rect.x+20, objectives_rect.bottom-28, objectives_rect.width-40, 10)
        self.draw_progress_bar(progress_bar, self.state.current_step / len(self.current_case.puzzle_steps))

        hint_lines = list(self.current_case.terminal_tips)+[""]+list(GLOBAL_TERMINAL_TIPS)
        self.draw_scrollable_text(
            "case_hints",
            hint_lines,
            pygame.Rect(hints_rect.x + 20, hints_rect.y + 42, hints_rect.width - 40, hints_rect.height - 62),
            self.small_font,
            (192, 228, 221),
        )

        status_rect = pygame.Rect(terminal_rect.x+18, terminal_rect.y+42, terminal_rect.width-36, 44)
        status_lines = [
            f"{self.current_case.title} | Case {self.case_index+1}/{len(self.cases)} | Time {self.format_duration(self.get_active_elapsed_seconds())}",
            f"Mistakes {self.state.wrong_answers} | Commands { self.state.commands_used}"
        ]
        self.draw_wrapped_text(status_lines, status_rect, self.small_font, (150, 219, 198))

        history_rect = pygame.Rect(terminal_rect.x+18, terminal_rect.y+92, terminal_rect.width-36, terminal_rect.height-166)
        self.command_bar = pygame.Rect(terminal_rect.x+18, terminal_rect.bottom-58, terminal_rect.width-36, 44)
        self.draw_terminal_history(history_rect)
        self.draw_command_input(self.command_bar)

    def draw_case_complete(self) -> None:
        width, height = self.screen.get_size()
        panel = pygame.Rect(80, 72, width - 160, height - 144)
        self.draw_panel(panel, "Case Resolved")
        if self.last_result is None:
            return

        title = self.title_font.render(f"{self.current_case.code_name} CLOSED", True, (91, 241, 196))
        self.screen.blit(title, (panel.x + 24, panel.y + 40))

        gap = 16
        card_width = (panel.width - 48 - gap * 2) // 3
        cards_y = panel.y + 120
        self.draw_metric_card(pygame.Rect(panel.x + 24, cards_y, card_width, 90), "Time", self.format_duration(self.last_result.elapsed_seconds))
        self.draw_metric_card(pygame.Rect(panel.x + 24 + card_width + gap, cards_y, card_width, 90), "Mistakes", str(self.last_result.wrong_answers))
        self.draw_metric_card(pygame.Rect(panel.x + 24 + (card_width + gap) * 2, cards_y, card_width, 90), "Score", str(self.last_result.score))

        summary_rect = pygame.Rect(panel.x + 24, cards_y + 118, panel.width - 48, 130)
        summary_lines = list(self.current_case.completion_lines) + ["", f"You solved the case with {self.last_result.commands_used} terminal commands."]
        self.draw_scrollable_text("case_complete_summary", summary_lines, summary_rect, self.body_font, (227, 247, 242))

        if self.case_index + 1 < len(self.cases):
            preview_rect = pygame.Rect(panel.x + 24, panel.bottom - 168, panel.width - 48, 88)
            self.draw_case_card(preview_rect, self.cases[self.case_index + 1], "Up Next")
            footer_lines = ["Press Enter for the next case, R to replay this one, or Esc for the menu."]
        else:
            footer_lines = ["All cases cleared. Press Enter to view the campaign summary, R to replay, or Esc for the menu."]

        footer_rect = pygame.Rect(panel.x + 24, panel.bottom - 62, panel.width - 48, 36)
        self.draw_wrapped_text(footer_lines, footer_rect, self.small_font, (145, 198, 188))

    def draw_game_complete(self) -> None:
        width, height = self.screen.get_size()
        panel = pygame.Rect(56, 56, width - 112, height - 112)
        self.draw_panel(panel, "Campaign Complete")

        title = self.title_font.render("Cipher High Secured", True, (91, 241, 196))
        self.screen.blit(title, (panel.x + 24, panel.y + 36))

        total_score = sum(result.score for result in self.results)
        total_time = sum(result.elapsed_seconds for result in self.results)
        total_mistakes = sum(result.wrong_answers for result in self.results)
        metric_width = (panel.width - 48 - 14 * 3) // 4
        cards_y = panel.y + 108
        metrics = [
            ("Rating", self.get_campaign_rating(total_score)),
            ("Score", str(total_score)),
            ("Total Time", self.format_duration(total_time)),
            ("Mistakes", str(total_mistakes)),
        ]
        for index, (label, value) in enumerate(metrics):
            rect = pygame.Rect(panel.x + 24 + index * (metric_width + 14), cards_y, metric_width, 90)
            self.draw_metric_card(rect, label, value)

        results_y = cards_y + 118
        result_width = (panel.width - 48 - 16 * 2) // 3
        for index, result in enumerate(self.results):
            rect = pygame.Rect(panel.x + 24 + index * (result_width + 16), results_y, result_width, 170)
            self.draw_result_card(rect, result)

        footer_rect = pygame.Rect(panel.x + 24, panel.bottom - 96, panel.width - 48, 60)
        footer_lines = [
            "You completed the full mini campaign and proved the prototype works as a small submission-ready game.",
            "Press Enter to restart the campaign or Esc to return to the menu.",
        ]
        self.draw_wrapped_text(footer_lines, footer_rect, self.small_font, (205, 229, 226))

    def draw_panel(self, rect: pygame.Rect, title: str) -> None:
        pygame.draw.rect(self.screen, (10, 18, 26), rect, border_radius=14)
        pygame.draw.rect(self.screen, (91, 241, 196), rect, width=2, border_radius=14)
        title_surface = self.small_font.render(title.upper(), True, (91, 241, 196))
        self.screen.blit(title_surface, (rect.x + 18, rect.y + 14))

    def draw_case_card(self, rect: pygame.Rect, case: CaseData, status: str) -> None:
        pygame.draw.rect(self.screen, (14, 25, 34), rect, border_radius=12)
        pygame.draw.rect(self.screen, (65, 165, 142), rect, width=2, border_radius=12)
        header = self.small_font.render(case.code_name, True, (91, 241, 196))
        status_surface = self.small_font.render(status.upper(), True, (234, 255, 250))
        self.screen.blit(header, (rect.x + 16, rect.y + 16))
        self.screen.blit(status_surface, (rect.right - status_surface.get_width() - 16, rect.y + 16))

        title_surface = self.body_font.render(case.title, True, (232, 248, 245))
        self.screen.blit(title_surface, (rect.x + 16, rect.y + 52))

        blurb_rect = pygame.Rect(rect.x + 16, rect.y + 92, rect.width - 32, rect.height - 108)
        self.draw_scrollable_text(f"{self.scene}_case_card_{case.code_name}", [case.menu_blurb], blurb_rect, self.small_font, (188, 223, 214))

    def draw_metric_card(self, rect: pygame.Rect, label: str, value: str) -> None:
        pygame.draw.rect(self.screen, (13, 24, 33), rect, border_radius=12)
        pygame.draw.rect(self.screen, (91, 241, 196), rect, width=2, border_radius=12)
        label_surface = self.small_font.render(label.upper(), True, (155, 214, 198))
        self.screen.blit(label_surface, (rect.x + 14, rect.y + 14))

        font = self.metric_font if self.metric_font.size(value)[0] <= rect.width - 28 else self.body_font
        value_surface = font.render(value, True, (237, 255, 251))
        self.screen.blit(value_surface, (rect.x + 14, rect.y + 42))

    def draw_result_card(self, rect: pygame.Rect, result: CaseResult) -> None:
        pygame.draw.rect(self.screen, (14, 25, 34), rect, border_radius=12)
        pygame.draw.rect(self.screen, (65, 165, 142), rect, width=2, border_radius=12)

        code_surface = self.small_font.render(result.code_name, True, (91, 241, 196))
        self.screen.blit(code_surface, (rect.x + 14, rect.y + 14))

        title_surface = self.body_font.render(result.title, True, (237, 255, 251))
        self.screen.blit(title_surface, (rect.x + 14, rect.y + 44))

        summary_lines = [
            f"Score: {result.score}",
            f"Time: {self.format_duration(result.elapsed_seconds)}",
            f"Mistakes: {result.wrong_answers}",
            f"Commands: {result.commands_used}",
        ]
        summary_rect = pygame.Rect(rect.x + 14, rect.y + 84, rect.width - 28, rect.height - 96)
        self.draw_scrollable_text(f"{self.scene}_result_card_{result.case_number}", summary_lines, summary_rect, self.small_font, (188, 223, 214))

    def draw_progress_bar(self, rect: pygame.Rect, progress: float) -> None:
        pygame.draw.rect(self.screen, (19, 33, 43), rect, border_radius=6)
        filled = rect.copy()
        filled.width = int(rect.width * max(0.0, min(progress, 1.0)))
        if filled.width > 0:
            pygame.draw.rect(self.screen, (91, 241, 196), filled, border_radius=6)

    def draw_command_input(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (9, 17, 23), rect, border_radius=10)
        pygame.draw.rect(self.screen, (91, 241, 196), rect, width=2, border_radius=10)

        prompt_surface = self.body_font.render("> ", True, (234, 255, 250))
        prompt_x = rect.x + 12
        prompt_y = rect.y + 9
        self.screen.blit(prompt_surface, (prompt_x, prompt_y))

        input_x = prompt_x + prompt_surface.get_width()
        available_width = rect.width - 24 - prompt_surface.get_width()
        display_text, cursor_offset = self.get_input_display(self.state.current_input, self.state.cursor_index, self.body_font, available_width)
        text_surface = self.body_font.render(display_text, True, (234, 255, 250))
        self.screen.blit(text_surface, (input_x, prompt_y))

        if self.cursor_visible:
            cursor_x = input_x + cursor_offset
            pygame.draw.line(self.screen, (91, 241, 196), (cursor_x, rect.y + 10), (cursor_x, rect.y + 34), 2)

    def draw_scrollable_text(
    self,
    region_id: str,
    lines: list[str],
    rect: pygame.Rect,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    accent_first_line: bool = False,
    ) -> None:
        scrollbar_width = 10
        scrollbar_gap = 10
        text_rect = pygame.Rect(rect.x, rect.y, rect.width - scrollbar_width - scrollbar_gap, rect.height)
        prepared_lines = self.wrap_lines(lines, font, text_rect.width)
        line_height = font.get_linesize() + 4
        total_height = len(prepared_lines) * line_height
        max_offset = max(0, total_height - text_rect.height)
        offset = max(0, min(self.scroll_offsets.get(region_id, 0), max_offset))
        self.scroll_offsets[region_id] = offset
        self.scroll_regions[region_id] = {"viewport": rect.copy(), "max_offset": max_offset}

        old_clip = self.screen.get_clip()
        self.screen.set_clip(text_rect)
        y = text_rect.y - offset
        for index, line in enumerate(prepared_lines):
            if not line:
                y += line_height
                continue
            if y + line_height >= text_rect.y and y <= text_rect.bottom:
                line_color = (91, 241, 196) if accent_first_line and index == 0 else color
                surface = font.render(line, True, line_color)
                self.screen.blit(surface, (text_rect.x, y))
            y += line_height
        self.screen.set_clip(old_clip)

        track_rect = pygame.Rect(rect.right - scrollbar_width, rect.y, scrollbar_width, rect.height)
        pygame.draw.rect(self.screen, (21, 35, 44), track_rect, border_radius=6)
        if max_offset == 0:
            thumb_rect = track_rect.copy()
        else:
            thumb_height = max(28, int(rect.height * (rect.height / total_height)))
            travel = rect.height - thumb_height
            thumb_y = rect.y + int((offset / max_offset) * travel)
            thumb_rect = pygame.Rect(track_rect.x, thumb_y, scrollbar_width, thumb_height)
        pygame.draw.rect(self.screen, (91, 241, 196), thumb_rect, border_radius=6)

    def draw_wrapped_text(
        self,
        lines: list[str],
        rect: pygame.Rect,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        accent_first_line: bool = False,
    ) -> None:
        prepared_lines = self.wrap_lines(lines, font, rect.width)
        line_height = font.get_linesize() + 4
        y = rect.y
        max_bottom = rect.y + rect.height
        for index, line in enumerate(prepared_lines):
            if y + line_height > max_bottom:
                break
            if not line:
                y += line_height
                continue
            line_color = (91, 241, 196) if accent_first_line and index == 0 else color
            surface = font.render(line, True, line_color)
            self.screen.blit(surface, (rect.x, y))
            y += line_height


    def wrap_lines(self, lines: list[str], font: pygame.font.Font, max_width: int) -> list[str]:
        wrapped: list[str] = []
        for raw_line in lines:
            if not raw_line:
                wrapped.append("")
                continue
            words = raw_line.split(" ")
            current_line = ""
            for word in words:
                if not word and not current_line:
                    continue
                test_line = f"{current_line} {word}".strip()
                if current_line and font.size(test_line)[0] > max_width:
                    wrapped.append(current_line)
                    current_line = self.break_long_word(word, font, max_width)
                    if "\n" in current_line:
                        parts = current_line.split("\n")
                        wrapped.extend(parts[:-1])
                        current_line = parts[-1]
                else:
                    if font.size(word)[0] > max_width:
                        broken_word = self.break_long_word(word, font, max_width)
                        if current_line:
                            wrapped.append(current_line)
                            current_line = ""
                        parts = broken_word.split("\n")
                        wrapped.extend(parts[:-1])
                        current_line = parts[-1]
                    else:
                        current_line = test_line
            if current_line:
                wrapped.append(current_line)
        return wrapped

    def break_long_word(self, word: str, font: pygame.font.Font, max_width: int) -> str:
        chunks: list[str] = []
        current = ""
        for character in word:
            test = current + character
            if current and font.size(test)[0] > max_width:
                chunks.append(current)
                current = character
            else:
                current = test
        if current:
            chunks.append(current)
        return "\n".join(chunks)

    def draw_terminal_history(self, rect: pygame.Rect) -> None:
        wrapped_history = self.wrap_lines(self.state.history, self.small_font, rect.width)
        line_height = self.small_font.get_linesize() + 4
        max_lines = max(1, rect.height // line_height)
        visible_lines = wrapped_history[-max_lines:]
        y = rect.y
        for line in visible_lines:
            surface = self.small_font.render(line, True, (164, 242, 216))
            self.screen.blit(surface, (rect.x, y))
            y += line_height


    def get_input_display(
            self,
            text: str,
            cursor_index: int,
            font: pygame.font.Font,
            max_width: int,
    ) -> tuple[str, int]:
        if not text:
            return "", 0
        if font.size(text)[0] <= max_width:
            return text, font.size(text[:cursor_index])[0]
        
        start = cursor_index
        end = cursor_index
        while True:
            expanded = False
            if start > 0:
                candidate = self.decorate_input_view(text, start-1, end)
                if font.size(candidate)[0] <= max_width:
                    start-=1
                    expanded=True
            if end < len(text):
                candidate = self.decorate_input_view(text, start, end+1)
                if font.size(candidate)[0] <= max_width:
                    end+=1
                    expanded=True
            if not expanded:
                break
        
        display_text = self.decorate_input_view(text, start, end)
        cursor_prefix = ("..." if start >0 else "") + text[start:cursor_index]
        return display_text, font.size(cursor_prefix)[0]

    def decorate_input_view(self, text: str, start: int, end: int) -> str:
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{text[start:end]}{suffix}"

    def launch_from_menu(self) -> None:
        if not self.started:
            self.start_game()
            return
        if self.active_case_completed:
            if self.case_index+1 < len(self.cases):
                self.load_case(self.case_index +1)
            else:
                self.start_game()
            return

    def start_game(self) -> None:
        self.results = []
        self.last_result = None
        self.load_case(0)

    def load_case(self, case_index:int) -> None:
        self.case_index = case_index
        self.scene = "case"
        self.started = True
        self.active_case_completed = False
        self.state = TerminalState()
        self.case_started_ticks = pygame.time.get_ticks()
        self.add_history("System boot complete.")
        self.add_history(f"Connected to {self.current_case.code_name}.")
        self.add_history(self.current_case.menu_blurb)
        self.add_history("Type to help review commands, then inspect the evidence files.")
        self.add_history(self.current_case.puzzle_steps[0].prompt)

    def reset_case(self) -> None:
        self.load_case(self.case_index)

    def next_case(self) -> None:
        if self.case_index + 1 < len(self.cases):
            self.load_case(self.case_index + 1)
        else:
            self.scene = "game_complete"

    def add_history(self, line:str) -> None:
        self.state.history.append(line)

    def clear_input(self) -> None:
        self.state.current_input = ""
        self.state.cursor_index = 0
        self.state.history_index = None
        self.state.history_draft = ""

    def insert_text(self, text:str) -> None:
        cursor = self.state.cursor_index
        current = self.state.current_input
        self.state.current_input = current[:cursor] + text + current[cursor:]
        self.state.cursor_index += len(text)
        self.state.history_index = None

    def delete_backward(self) -> None:
        cursor = self.state.cursor_index
        if cursor == 0:
            return
        current = self.state.current_input
        self.state.current_input = current[:cursor-1] + current[cursor:]
        self.state.cursor_index -= 1
        self.state.history_index = None

    def delete_forward(self) -> None:
        cursor = self.state.cursor_index
        current = self.state.current_input
        if cursor >= len(current):
            return
        self.state.current_input = current[:cursor] + current[cursor+1:]
        self.state.history_index = None

    def format_duration(self, total_seconds:int) -> str:
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_game_rating(self, total_score: int) -> str:
        if total_score >= 270:
            return "A"
        if total_score >= 240:
            return "B"
        if total_score >= 210:
            return "C"
        return "D"

    def get_case_status(self, case_index : int) -> str:
        if case_index < len(self.results):
            return "Cleared"
        if self.started and case_index == self.case_index and not self.active_case_completed:
            return "Active"
        if case_index == len(self.results):
            return "Ready"
        return "Locked"
    
    def get_menu_action_label(self) -> str:
        if not self.started:
            return "Start Game"
        if self.active_case_completed:
            if self.case_index+1 < len(self.cases):
                return "Next Case"
            return "Restart Game"
        return "Resume Game"

    def get_active_elapsed_seconds(self) -> int:
        if self.case_started_ticks == 0:
            return 0
        return (pygame.time.get_ticks() - self.case_started_ticks) // 1000
    
    def calculate_score(self, elapsed_seconds: int, wrong_answers: int) -> int:
        return max(45, 100 - wrong_answers * 12 - (elapsed_seconds // 20) * 4)
    
    def finish_case(self) -> None:
        elapsed_seconds = max(1, self.get_active_elapsed_seconds())
        result = CaseResult(
            case_number=self.case_index+1,
            code_name=self.current_case.code_name,
            title=self.current_case.title,
            elapsed_seconds=elapsed_seconds,
            wrong_answers=self.state.wrong_answers,
            commands_used=self.state.commands_used,
            score=self.calculate_score(elapsed_seconds, self.state.wrong_answers)
        )

        if len(self.results) > self.case_index:
            self.results[self.case_index] = result
        else:
            self.results.append(result)

        self.last_result = result
        self.active_case_completed = True
        if self.case_index == len(self.cases) - 1:
            self.scene = "campaign_complete"
        else:
            self.scene = "case_complete"
    
    def submit_answer(self, answer:str) -> None:
        if not answer:
            self.add_history("Usage: submit <answer>")
            return
        
        step = self.current_case.puzzle_steps[self.state.current_step]
        normalized = answer.strip().lower()
        valid_answers = {step.answer.lower(), *[acceptable.lower() for acceptable in step.acceptable]}
        if normalized not in valid_answers:
            self.state.wrong_answers += 1
            self.add_history("Not quite. Review the evidence and try again.")
            return

        self.add_history(step.success_message)
        if self.state.current_step == len(self.current_case.puzzle_steps) -1:
            self.finish_case()
            return

        self.state.current_step += 1
        self.add_history(self.current_case.puzzle_steps[self.state.current_step].prompt)

    def decode_rot13(self, args:list[str]) -> None:
        if not args:
            self.add_history("Usage: rot13 <text>")
            return
        decoded = codecs.decode(" ".join(args), "rot_13")
        self.add_history(f"Decoded text: {decoded}")

    def base64_decode(self, encoded:str) -> str | None:
        padded = encoded + "=" * ((4-len(encoded) %4) %4)
        try: 
            return base64.b64decode(padded, validate=True).decode("utf-8")
        except Exception:
            return None
        
    def hex_decode(self, encoded:str) -> str | None:
        if len(encoded) %2 != 0:
            return None
        if not encoded or any(character not in "0123456789abcedfABCDEF" for character in encoded):
            return None
        try:
            return bytes.fromhex(encoded).decode("utf-8")
        except ValueError:
            return None
        
    def decode_text(self, args:list[str]) -> None:
        if not args:
            self.add_history("Usage: decode <text>")
            return

        encoded = "".join(args)
        decoded = self.hex_decode(encoded)
        if decoded is None:
            decoded = self.base64_decode(encoded)
            
        if decoded is None:
            self.add_history("Decode failed, This command supports base64 and hex clues only.")
            return
        self.add_history(f"Decoded text: {decoded}")

    def open_file(self, args:list[str]) -> None:
        if not args:
            self.add_history("Usage: open <file>")
            return
        filename = args[0]
        content = self.current_case.evidence_files.get(filename)
        if content is None:
            self.add_history(f"File not found: {filename}")
            return
        self.add_history(f"-------{filename}-------")
        for line in content:
            self.add_history(line)

    def show_help(self) -> None:
        help_lines = [
            "help --               Show available commands.",
            "files --              List evidence files.",
            "open <file> --        Read an evidence file.",
            "decode <text> --      Auto-decode base64 or hex clues.",
            "rot13 <text> --       Decode a ROT13 clue.",
            "submit <answer> --    Submit the current answer.",
            "status --             Repeat the current objective.",
            "clear --              Clear terminal history.",
            "Controls --           Left/Right/Home/End edit input. Up/Down recall commands."
        ]
        for line in help_lines:
            self.add_history(line)

    def execute_command(self, command:str) -> None:
        self.state.commands_used +=1
        if not self.state.command_history or self.state.command_history[-1] != command:
            self.state.command_history.append(command)
        self.state.history_index = None
        self.state.history_draft = ""

        self.add_history(f"> {command}")
        parts = command.split()
        keyword = parts[0].lower()
        args = parts[1:]

        if keyword == "help":
            self.show_help()
        elif keyword == "clear":
            self.state.history.clear()
            self.add_history(f"{self.current_case.code_name} // terminal cleared.")
        elif keyword == "files":
            self.add_history("Evidence files: " + ", ".join(self.current_case.evidence_files.keys()))
        elif keyword == "open":
            self.open_file(args)
        elif keyword == "decode":
            self.decode_text(args)
        elif keyword == "rot13":
            self.decode_rot13(args)
        elif keyword == "submit":
            self.submit_answer(" ".join(args))
        elif keyword == "status":
            self.add_history(self.current_case.puzzle_steps[self.state.current_step].prompt)
        else:
            self.add_history("Unknwon command. Type help for the valid command list.")

    def browse_history(self, direction:int) -> None:
        if not self.state.command_history:
            return

        if self.state.history_index is None:
            if direction < 0:
                self.state.history_draft = self.state.current_input
                self.state.history_index = len(self.state.command_history) - 1
            else:
                return
        else:
            next_index = self.state.history_index + direction
            if next_index < 0:
                next_index = 0
            elif next_index >= len(self.state.command_history):
                self.state.history_index = None
                self.state.current_input = self.state.history_draft
                self.state.cursor_index = len(self.state.current_input)
                return
            self.state.history_index = next_index

        entry = self.state.command_history[self.state.history_index]
        self.state.current_input = entry
        self.state.cursor_index = len(entry)
            
    def move_cursor(self, delta:int) -> None:
        cursor = self.state.cursor_index + delta
        self.state.cursor_index = max(0, min(len(self.state.current_input), cursor))

   