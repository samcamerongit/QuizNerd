from __future__ import annotations

import random
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox

from quiznerd_data import SEED_QUESTIONS

APP_DIR = Path(__file__).resolve().parent


def resolve_data_dir(script_dir: Path) -> Path:
  # When QuizNerd runs from a macOS app bundle, keep writable data out of the bundle.
  if (
    script_dir.name == "Resources"
    and script_dir.parent.name == "Contents"
    and script_dir.parent.parent.suffix == ".app"
  ):
    support_dir = Path.home() / "Library" / "Application Support" / "QuizNerd"
    support_dir.mkdir(parents=True, exist_ok=True)
    return support_dir
  return script_dir


DATA_DIR = resolve_data_dir(APP_DIR)
DB_PATH = DATA_DIR / "quiznerd.db"

BASE_WIDTH = 980
BASE_HEIGHT = 840
MIN_WIDTH = 840
MIN_HEIGHT = 700

APP_TAGLINE = "Offline general knowledge quiz."
COPYRIGHT_TEXT = "Copyright ©2026, Sam Cameron. All rights reserved."

COLORS = {
  "bg": "#ffffff",
  "surface": "#fbfbfb",
  "surface_alt": "#f3f3f3",
  "line": "#dddddd",
  "text": "#111111",
  "muted": "#6b7280",
  "black": "#111111",
  "white": "#ffffff",
  "disabled_bg": "#efefef",
  "disabled_line": "#e5e5e5",
  "disabled_text": "#9aa0a6",
  "success_bg": "#eef8f1",
  "success_line": "#2e8b57",
  "danger_bg": "#fff2f2",
  "danger_line": "#d14c4c",
}

FONT_SPECS = {
  "brand": {"size": 30, "weight": "bold"},
  "subtitle": {"size": 13, "weight": "normal"},
  "page": {"size": 21, "weight": "bold"},
  "prompt": {"size": 20, "weight": "bold"},
  "body": {"size": 12, "weight": "normal"},
  "meta": {"size": 10, "weight": "bold"},
  "button_title": {"size": 15, "weight": "bold"},
  "button_subtitle": {"size": 11, "weight": "normal"},
}


def clamp(value: int, minimum: int, maximum: int) -> int:
  return max(minimum, min(value, maximum))


class QuizDatabase:
  def __init__(self, path: Path) -> None:
    self.path = path
    self.path.parent.mkdir(parents=True, exist_ok=True)
    self._bootstrap()

  def _connect(self) -> sqlite3.Connection:
    connection = sqlite3.connect(self.path)
    connection.row_factory = sqlite3.Row
    return connection

  def _bootstrap(self) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          topic TEXT NOT NULL,
          question_type TEXT NOT NULL,
          prompt TEXT NOT NULL,
          answer TEXT NOT NULL,
          option_a TEXT,
          option_b TEXT,
          option_c TEXT,
          option_d TEXT,
          explanation TEXT NOT NULL DEFAULT ''
        )
        """
      )

      total = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
      if total == 0:
        connection.executemany(
          """
          INSERT INTO questions (
            topic,
            question_type,
            prompt,
            answer,
            option_a,
            option_b,
            option_c,
            option_d,
            explanation
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
          """,
          [self._to_record(question) for question in SEED_QUESTIONS],
        )

  def _to_record(self, question: dict) -> tuple:
    options = list(question.get("options", []))
    padded = (options + [None, None, None, None])[:4]
    return (
      question["topic"],
      question["question_type"],
      question["prompt"],
      question["answer"],
      padded[0],
      padded[1],
      padded[2],
      padded[3],
      question.get("explanation", ""),
    )

  def get_questions(self, topic: str) -> list[dict]:
    with self._connect() as connection:
      rows = connection.execute(
        """
        SELECT topic, question_type, prompt, answer, option_a, option_b, option_c, option_d, explanation
        FROM questions
        WHERE topic = ?
        ORDER BY id
        """,
        (topic,),
      ).fetchall()

    questions = []
    for row in rows:
      if row["question_type"] == "true_false":
        options = ["True", "False"]
      else:
        options = [row["option_a"], row["option_b"], row["option_c"], row["option_d"]]
        options = [option for option in options if option]

      questions.append(
        {
          "topic": row["topic"],
          "question_type": row["question_type"],
          "prompt": row["prompt"],
          "answer": row["answer"],
          "options": options,
          "explanation": row["explanation"],
        }
      )

    return questions


class HoverButton(tk.Frame):
  def __init__(
    self,
    parent: tk.Misc,
    fonts: dict[str, tkfont.Font],
    title: str,
    subtitle: str = "",
    command=None,
    compact: bool = False,
  ) -> None:
    super().__init__(
      parent,
      bg=COLORS["surface"],
      highlightthickness=1,
      highlightbackground=COLORS["line"],
      highlightcolor=COLORS["line"],
      bd=0,
      cursor="hand2" if command else "arrow",
    )
    self.fonts = fonts
    self.command = command
    self.compact = compact
    self.enabled = command is not None
    self.hovered = False
    self.variant = "default"

    outer_padx = 18 if compact else 22
    outer_pady = 12 if compact else 16

    self.columnconfigure(0, weight=1)

    self.inner = tk.Frame(self, bg=COLORS["surface"])
    self.inner.grid(row=0, column=0, sticky="ew", padx=outer_padx, pady=outer_pady)
    self.inner.columnconfigure(0, weight=1)

    self.title_label = tk.Label(
      self.inner,
      text=title,
      font=self.fonts["button_title"],
      bg=COLORS["surface"],
      fg=COLORS["text"],
      justify="center",
    )
    self.title_label.grid(row=0, column=0, sticky="ew")

    self.subtitle_label = tk.Label(
      self.inner,
      text=subtitle,
      font=self.fonts["button_subtitle"],
      bg=COLORS["surface"],
      fg=COLORS["muted"],
      justify="center",
    )
    self.subtitle_label.grid(row=1, column=0, sticky="ew", pady=(5, 0))

    self._bind_recursive(self)
    self._apply_style()

  def _bind_recursive(self, widget: tk.Misc) -> None:
    widget.bind("<Enter>", self._on_enter)
    widget.bind("<Leave>", self._on_leave)
    widget.bind("<Button-1>", self._on_click)
    for child in widget.winfo_children():
      self._bind_recursive(child)

  def _on_enter(self, _event=None) -> None:
    if not self.enabled:
      return
    self.hovered = True
    self._apply_style()

  def _on_leave(self, _event=None) -> None:
    if not self.enabled:
      return
    pointer_x, pointer_y = self.winfo_pointerxy()
    widget = self.winfo_containing(pointer_x, pointer_y)
    current = widget
    inside = False
    while current is not None:
      if current is self:
        inside = True
        break
      current = getattr(current, "master", None)
    if inside:
      return
    self.hovered = False
    self._apply_style()

  def _on_click(self, _event=None) -> None:
    if self.enabled and self.command:
      self.command()

  def _palette(self) -> dict[str, str]:
    if self.variant == "correct":
      return {
        "bg": COLORS["success_bg"],
        "line": COLORS["success_line"],
        "title": COLORS["text"],
        "subtitle": COLORS["success_line"],
      }

    if self.variant == "wrong":
      return {
        "bg": COLORS["danger_bg"],
        "line": COLORS["danger_line"],
        "title": COLORS["text"],
        "subtitle": COLORS["danger_line"],
      }

    if not self.enabled:
      return {
        "bg": COLORS["disabled_bg"],
        "line": COLORS["disabled_line"],
        "title": COLORS["disabled_text"],
        "subtitle": COLORS["disabled_text"],
      }

    if self.hovered:
      return {
        "bg": COLORS["black"],
        "line": COLORS["black"],
        "title": COLORS["white"],
        "subtitle": "#dddddd",
      }

    return {
      "bg": COLORS["surface"],
      "line": COLORS["line"],
      "title": COLORS["text"],
      "subtitle": COLORS["muted"],
    }

  def _apply_style(self) -> None:
    palette = self._palette()
    cursor = "hand2" if self.enabled and self.command else "arrow"

    self.configure(
      bg=palette["bg"],
      highlightbackground=palette["line"],
      highlightcolor=palette["line"],
      cursor=cursor,
    )
    self.inner.configure(bg=palette["bg"], cursor=cursor)
    self.title_label.configure(bg=palette["bg"], fg=palette["title"], cursor=cursor)
    self.subtitle_label.configure(bg=palette["bg"], fg=palette["subtitle"], cursor=cursor)

  def set_wraplength(self, wraplength: int) -> None:
    self.title_label.configure(wraplength=wraplength)
    self.subtitle_label.configure(wraplength=wraplength)

  def set_enabled(self, enabled: bool) -> None:
    self.enabled = enabled
    if not enabled:
      self.hovered = False
    self._apply_style()

  def set_variant(self, variant: str) -> None:
    self.variant = variant
    self.hovered = False
    self._apply_style()

  def set_text(self, title: str, subtitle: str = "") -> None:
    self.title_label.configure(text=title)
    self.subtitle_label.configure(text=subtitle)


class QuizNerdApp(tk.Tk):
  def __init__(self) -> None:
    super().__init__()
    self.title("QuizNerd")
    self.geometry(f"{BASE_WIDTH}x{BASE_HEIGHT}")
    self.minsize(MIN_WIDTH, MIN_HEIGHT)
    self.configure(bg=COLORS["bg"])

    self.database = QuizDatabase(DB_PATH)
    self.current_mode = "solo"
    self.current_topic = "general"
    self.questions: list[dict] = []
    self.current_index = 0
    self.score = 0
    self.answer_locked = False

    self.fonts = self.create_fonts()
    self.wrap_items: list[tuple[object, int, int]] = []

    self.option_buttons: list[HoverButton] = []
    self.reveal_button: HoverButton | None = None
    self.next_button: HoverButton | None = None
    self.feedback_label: tk.Label | None = None
    self.explanation_label: tk.Label | None = None
    self.answer_label: tk.Label | None = None
    self.answer_hint_label: tk.Label | None = None

    self.grid_columnconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=1)

    self.build_header()
    self.build_body()
    self.build_footer()

    self.bind("<Configure>", self._on_window_resize)
    self.after(120, self.present_window)
    self.show_home()

  def create_fonts(self) -> dict[str, tkfont.Font]:
    fonts: dict[str, tkfont.Font] = {}
    for key, spec in FONT_SPECS.items():
      fonts[key] = tkfont.Font(
        family="Avenir Next",
        size=spec["size"],
        weight=spec["weight"],
      )
    return fonts

  def build_header(self) -> None:
    self.header = tk.Frame(self, bg=COLORS["surface_alt"], highlightthickness=1, highlightbackground=COLORS["line"])
    self.header.grid(row=0, column=0, sticky="ew")
    self.header.grid_columnconfigure(0, weight=1)

    header_inner = tk.Frame(self.header, bg=COLORS["surface_alt"])
    header_inner.grid(row=0, column=0, pady=(18, 16))
    header_inner.grid_columnconfigure(0, weight=1)

    self.brand_label = tk.Label(
      header_inner,
      text="QuizNerd",
      font=self.fonts["brand"],
      fg=COLORS["text"],
      bg=COLORS["surface_alt"],
      justify="center",
    )
    self.brand_label.grid(row=0, column=0)

    self.subtitle_label = tk.Label(
      header_inner,
      text=APP_TAGLINE,
      font=self.fonts["subtitle"],
      fg=COLORS["muted"],
      bg=COLORS["surface_alt"],
      justify="center",
    )
    self.subtitle_label.grid(row=1, column=0, pady=(8, 0))

    self._track_wrap(self.subtitle_label, 120, 760)

  def build_body(self) -> None:
    self.body = tk.Frame(self, bg=COLORS["bg"])
    self.body.grid(row=1, column=0, sticky="nsew")
    self.body.grid_columnconfigure(0, weight=1)
    self.body.grid_rowconfigure(0, weight=1)

    self.body_canvas = tk.Canvas(
      self.body,
      bg=COLORS["bg"],
      highlightthickness=0,
      bd=0,
      yscrollincrement=18,
    )
    self.body_canvas.grid(row=0, column=0, sticky="nsew", padx=(26, 10), pady=(20, 0))

    self.scrollbar = tk.Scrollbar(self.body, orient="vertical", command=self.body_canvas.yview)
    self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 18), pady=(20, 0))
    self.body_canvas.configure(yscrollcommand=self.scrollbar.set)

    self.body_content = tk.Frame(self.body_canvas, bg=COLORS["bg"])
    self.body_window = self.body_canvas.create_window((0, 0), window=self.body_content, anchor="n")

    self.body_content.bind("<Configure>", self._on_body_content_configure)
    self.body_canvas.bind("<Configure>", self._on_body_canvas_configure)
    self.body_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    self.body_canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
    self.body_canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

  def build_footer(self) -> None:
    self.footer = tk.Frame(self, bg=COLORS["bg"])
    self.footer.grid(row=2, column=0, sticky="ew")
    self.footer.grid_columnconfigure(0, weight=1)

  def present_window(self) -> None:
    self.deiconify()
    self.lift()
    try:
      self.focus_force()
    except tk.TclError:
      return

  def _on_window_resize(self, _event=None) -> None:
    self.after_idle(self.refresh_wraps)

  def _is_descendant(self, widget: tk.Misc | None, ancestor: tk.Misc) -> bool:
    current = widget
    while current is not None:
      if current is ancestor:
        return True
      current = getattr(current, "master", None)
    return False

  def _pointer_is_in_body(self) -> bool:
    widget = self.winfo_containing(*self.winfo_pointerxy())
    return self._is_descendant(widget, self.body)

  def _can_scroll_body(self) -> bool:
    return self.body_content.winfo_reqheight() > self.body_canvas.winfo_height() + 1

  def _on_mousewheel(self, event) -> None:
    if not self._can_scroll_body() or not self._pointer_is_in_body():
      return
    if event.delta == 0:
      return
    units = -1 if event.delta > 0 else 1
    self.body_canvas.yview_scroll(units, "units")

  def _on_mousewheel_linux(self, event) -> None:
    if not self._can_scroll_body() or not self._pointer_is_in_body():
      return
    if event.num == 4:
      self.body_canvas.yview_scroll(-1, "units")
    elif event.num == 5:
      self.body_canvas.yview_scroll(1, "units")

  def _on_body_content_configure(self, _event=None) -> None:
    self.body_canvas.configure(scrollregion=self.body_canvas.bbox("all"))
    self.refresh_wraps()

  def _on_body_canvas_configure(self, event) -> None:
    content_width = self.content_width(event.width)
    self.body_canvas.coords(self.body_window, event.width / 2, 0)
    self.body_canvas.itemconfigure(self.body_window, width=content_width)
    self.after_idle(self.refresh_wraps)

  def content_width(self, canvas_width: int | None = None) -> int:
    if canvas_width is None:
      canvas_width = max(self.body_canvas.winfo_width(), 1)
    return clamp(canvas_width - 24, 560, 820)

  def _track_wrap(self, widget: object, margin: int, maximum: int) -> None:
    self.wrap_items.append((widget, margin, maximum))

  def refresh_wraps(self) -> None:
    content_width = self.content_width()
    for widget, margin, maximum in self.wrap_items:
      wraplength = clamp(content_width - margin, 220, maximum)
      if isinstance(widget, HoverButton):
        widget.set_wraplength(wraplength)
      else:
        try:
          widget.configure(wraplength=wraplength)
        except tk.TclError:
          continue

  def set_subtitle(self, text: str) -> None:
    self.subtitle_label.configure(text=text)
    self.refresh_wraps()

  def clear_screen(self) -> tk.Frame:
    for child in self.body_content.winfo_children():
      child.destroy()
    for child in self.footer.winfo_children():
      child.destroy()

    self.body_canvas.yview_moveto(0)
    self.body_canvas.configure(scrollregion=(0, 0, self.body_canvas.winfo_width(), 0))

    self.wrap_items = []
    self._track_wrap(self.subtitle_label, 120, 760)

    self.option_buttons = []
    self.reveal_button = None
    self.next_button = None
    self.feedback_label = None
    self.explanation_label = None
    self.answer_label = None
    self.answer_hint_label = None

    page = tk.Frame(self.body_content, bg=COLORS["bg"])
    page.pack(fill="x")
    return page

  def make_panel(self, parent: tk.Misc, soft: bool = False) -> tk.Frame:
    panel = tk.Frame(
      parent,
      bg=COLORS["surface_alt"] if soft else COLORS["surface"],
      highlightthickness=1,
      highlightbackground=COLORS["line"],
      bd=0,
      padx=20,
      pady=16,
    )
    panel.pack(fill="x")
    return panel

  def add_text(
    self,
    parent: tk.Misc,
    text: str,
    font_key: str,
    fg: str,
    pady: tuple[int, int] = (0, 0),
    maximum: int = 720,
  ) -> tk.Label:
    label = tk.Label(
      parent,
      text=text,
      font=self.fonts[font_key],
      fg=fg,
      bg=parent.cget("bg"),
      justify="center",
    )
    label.pack(fill="x", pady=pady)
    self._track_wrap(label, 80, maximum)
    return label

  def make_button(
    self,
    parent: tk.Misc,
    title: str,
    subtitle: str,
    command,
    compact: bool = False,
  ) -> HoverButton:
    button = HoverButton(parent, self.fonts, title=title, subtitle=subtitle, command=command, compact=compact)
    button.pack(fill="x")
    self._track_wrap(button, 92, 700)
    return button

  def set_home_footer(self) -> None:
    self.footer.configure(bg=COLORS["surface_alt"])

    divider = tk.Frame(self.footer, bg=COLORS["line"], height=1)
    divider.pack(fill="x", side="top")

    label = tk.Label(
      self.footer,
      text=COPYRIGHT_TEXT,
      font=self.fonts["body"],
      fg=COLORS["muted"],
      bg=COLORS["surface_alt"],
      anchor="w",
      justify="left",
      padx=30,
      pady=16,
    )
    label.pack(fill="x")
    self._track_wrap(label, 140, 880)

  def set_action_footer(
    self,
    primary: tuple[str, callable, bool] | None = None,
    secondary: tuple[str, callable, bool] | None = None,
  ) -> None:
    self.footer.configure(bg=COLORS["bg"])

    outer = tk.Frame(self.footer, bg=COLORS["bg"])
    outer.pack(fill="x", padx=26, pady=(10, 22))

    row = tk.Frame(outer, bg=COLORS["bg"])
    row.pack(fill="x")
    row.grid_columnconfigure(0, weight=1)
    row.grid_columnconfigure(1, weight=1)

    if secondary and primary:
      back_label, back_command, back_enabled = secondary
      next_label, next_command, next_enabled = primary

      back_button = HoverButton(row, self.fonts, title=back_label, subtitle="", command=back_command, compact=True)
      back_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))
      back_button.set_enabled(back_enabled)
      self._track_wrap(back_button, 300, 280)

      next_button = HoverButton(row, self.fonts, title=next_label, subtitle="", command=next_command, compact=True)
      next_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))
      next_button.set_enabled(next_enabled)
      self._track_wrap(next_button, 300, 280)
      self.next_button = next_button
      return

    label, command, enabled = primary or secondary
    button = HoverButton(row, self.fonts, title=label, subtitle="", command=command, compact=True)
    button.grid(row=0, column=0, columnspan=2, sticky="ew")
    button.set_enabled(enabled)
    self._track_wrap(button, 300, 320)
    if primary:
      self.next_button = button

  def meta_text(self) -> str:
    items = [
      self.current_mode.title(),
      "General",
      f"Question {self.current_index + 1} of {len(self.questions)}",
    ]
    if self.current_mode == "solo":
      items.append(f"Score {self.score}")
    return "  •  ".join(items)

  def show_home(self) -> None:
    page = self.clear_screen()
    self.set_subtitle(APP_TAGLINE)

    self.add_text(
      page,
      "Choose how you want to play. Solo keeps score. Multiplayer lets one person host the question and reveal the answer on tap.",
      "body",
      COLORS["muted"],
      pady=(14, 24),
      maximum=700,
    )

    panel = self.make_panel(page, soft=True)
    panel.pack_configure(pady=(0, 0))

    self.make_button(
      panel,
      "Solo",
      "Multiple choice and true / false general knowledge questions.",
      lambda: self.show_mode_menu("solo"),
    ).pack_configure(pady=(0, 12))

    self.make_button(
      panel,
      "Multiplayer",
      "Question first, answer reveal second, for clean quizmaster-style rounds.",
      lambda: self.show_mode_menu("multiplayer"),
    )

    self.set_home_footer()

  def show_mode_menu(self, mode: str) -> None:
    page = self.clear_screen()
    self.current_mode = mode

    if mode == "solo":
      self.set_subtitle("Solo mode mixes multiple choice and true / false and keeps score.")
      title = "Solo"
      description = "General knowledge across science, geography, history, sport, and quick-fire trivia."
    else:
      self.set_subtitle("Multiplayer mode shows the question first and reveals the answer on tap.")
      title = "Multiplayer"
      description = "General knowledge for a clean host-led question flow."

    self.add_text(page, title, "page", COLORS["text"], pady=(14, 8), maximum=520)
    self.add_text(page, "Right now there is one pack ready to play.", "body", COLORS["muted"], pady=(0, 22), maximum=560)

    panel = self.make_panel(page, soft=True)
    panel.pack_configure(pady=(0, 0))
    self.add_text(panel, "General", "page", COLORS["text"], pady=(0, 8), maximum=520)
    self.add_text(panel, description, "body", COLORS["muted"], pady=(0, 18), maximum=620)
    self.make_button(panel, "Play General", "Start a fresh shuffle.", lambda: self.start_round(mode, "general"))

    self.set_action_footer(secondary=("Back", self.show_home, True))

  def start_round(self, mode: str, topic: str) -> None:
    self.current_mode = mode
    self.current_topic = topic
    self.questions = self.database.get_questions(topic)

    if not self.questions:
      messagebox.showerror("QuizNerd", "There are no questions in the local database for this pack yet.")
      return

    random.shuffle(self.questions)
    for question in self.questions:
      random.shuffle(question["options"])
    self.current_index = 0
    self.score = 0
    self.answer_locked = False
    self.show_current_question()

  def show_current_question(self) -> None:
    if self.current_index >= len(self.questions):
      self.show_finish_screen()
      return

    question = self.questions[self.current_index]
    if self.current_mode == "solo":
      self.show_solo_question(question)
    else:
      self.show_multiplayer_question(question)

  def show_solo_question(self, question: dict) -> None:
    page = self.clear_screen()
    self.answer_locked = False
    self.set_subtitle("Solo mode mixes multiple choice and true / false and keeps score.")

    type_text = "TRUE / FALSE" if question["question_type"] == "true_false" else "MULTIPLE CHOICE"
    self.add_text(page, f"{self.meta_text()}  •  {type_text}", "meta", COLORS["muted"], pady=(4, 12), maximum=720)

    prompt_panel = self.make_panel(page, soft=True)
    prompt_panel.pack_configure(pady=(0, 12))
    self.add_text(prompt_panel, question["prompt"], "prompt", COLORS["text"], pady=(0, 0), maximum=680)

    options_frame = tk.Frame(page, bg=COLORS["bg"])
    options_frame.pack(fill="x")

    self.option_buttons = []
    for option_text in question["options"]:
      button = self.make_button(
        options_frame,
        option_text,
        "",
        lambda selected=option_text: self.select_solo_answer(question, selected),
      )
      button.pack_configure(pady=(0, 8))
      self.option_buttons.append(button)

    feedback_panel = self.make_panel(page, soft=False)
    feedback_panel.pack_configure(pady=(0, 0))
    self.feedback_label = self.add_text(
      feedback_panel,
      "Choose an answer to continue.",
      "button_title",
      COLORS["text"],
      pady=(0, 8),
      maximum=620,
    )
    self.explanation_label = self.add_text(
      feedback_panel,
      "",
      "body",
      COLORS["muted"],
      pady=(0, 0),
      maximum=620,
    )

    self.set_action_footer(
      secondary=("Back", lambda: self.show_mode_menu("solo"), True),
      primary=("Next", self.advance_question, False),
    )

  def select_solo_answer(self, question: dict, selected_option: str) -> None:
    if self.answer_locked:
      return

    self.answer_locked = True
    is_correct = selected_option == question["answer"]

    for button in self.option_buttons:
      option_title = button.title_label.cget("text")
      button.set_enabled(False)

      if option_title == question["answer"]:
        button.set_variant("correct")
        button.set_text(option_title, "Correct answer")
      else:
        button.set_variant("wrong")
        if option_title == selected_option:
          button.set_text(option_title, "Your pick")
        else:
          button.set_text(option_title, "Incorrect")

    if is_correct:
      self.score += 1
      if self.feedback_label:
        self.feedback_label.configure(text="Correct.", fg=COLORS["success_line"])
    else:
      if self.feedback_label:
        self.feedback_label.configure(
          text=f"Not quite. The correct answer is {question['answer']}.",
          fg=COLORS["danger_line"],
        )

    if self.explanation_label:
      self.explanation_label.configure(text=question["explanation"])

    if self.next_button:
      self.next_button.set_enabled(True)

  def show_multiplayer_question(self, question: dict) -> None:
    page = self.clear_screen()
    self.answer_locked = False
    self.set_subtitle("Multiplayer mode shows the question first and reveals the answer on tap.")

    self.add_text(page, self.meta_text(), "meta", COLORS["muted"], pady=(4, 12), maximum=720)

    self.reveal_button = self.make_button(
      page,
      question["prompt"],
      "Tap to reveal answer",
      lambda: self.reveal_answer(question),
    )
    self.reveal_button.pack_configure(pady=(0, 12))

    answer_panel = self.make_panel(page, soft=True)
    answer_panel.pack_configure(pady=(0, 0))
    self.add_text(answer_panel, "Answer", "meta", COLORS["muted"], pady=(0, 8), maximum=520)
    self.answer_label = self.add_text(
      answer_panel,
      "Waiting for reveal.",
      "prompt",
      COLORS["text"],
      pady=(0, 8),
      maximum=620,
    )
    self.answer_hint_label = self.add_text(
      answer_panel,
      "",
      "body",
      COLORS["muted"],
      pady=(0, 0),
      maximum=620,
    )

    self.set_action_footer(
      secondary=("Back", lambda: self.show_mode_menu("multiplayer"), True),
      primary=("Next", self.advance_question, False),
    )

  def reveal_answer(self, question: dict) -> None:
    if self.answer_locked:
      return

    self.answer_locked = True

    if self.reveal_button:
      self.reveal_button.set_enabled(False)
      self.reveal_button.set_text(question["prompt"], "Answer revealed below")

    if self.answer_label:
      self.answer_label.configure(text=question["answer"])

    if self.answer_hint_label:
      self.answer_hint_label.configure(text=question["explanation"])

    if self.next_button:
      self.next_button.set_enabled(True)

  def advance_question(self) -> None:
    if not self.answer_locked:
      return
    self.current_index += 1
    self.show_current_question()

  def show_finish_screen(self) -> None:
    page = self.clear_screen()

    if self.current_mode == "solo":
      self.set_subtitle("Solo round complete. Start again whenever you want a fresh shuffle.")
      subtitle = f"You scored {self.score} out of {len(self.questions)}."
      result = f"{self.score} / {len(self.questions)}"
    else:
      self.set_subtitle("Multiplayer round complete. Start again whenever you want a fresh shuffle.")
      subtitle = f"You reached the end of {len(self.questions)} questions."
      result = "All questions played"

    self.add_text(page, "Round complete", "page", COLORS["text"], pady=(18, 8), maximum=520)
    self.add_text(page, subtitle, "body", COLORS["muted"], pady=(0, 22), maximum=620)

    result_panel = self.make_panel(page, soft=True)
    result_panel.pack_configure(pady=(0, 0))
    self.add_text(result_panel, result, "brand", COLORS["text"], pady=(0, 8), maximum=520)
    self.add_text(result_panel, "Play again for a new order or head back home.", "body", COLORS["muted"], pady=(0, 0), maximum=620)

    self.set_action_footer(
      secondary=("Home", self.show_home, True),
      primary=("Play Again", lambda: self.start_round(self.current_mode, self.current_topic), True),
    )


def main() -> None:
  app = QuizNerdApp()
  app.mainloop()


if __name__ == "__main__":
  main()
