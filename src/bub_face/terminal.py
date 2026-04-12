from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Callable

import bub.channels.cli as cli_module
from prompt_toolkit.formatted_text import FormattedText
from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from bub.channels.cli import CliChannel as BubCliChannel
from bub.channels.cli.renderer import CliRenderer as BubCliRenderer
from bub.channels.message import ChannelMessage, MessageKind
from bub.envelope import field_of
from bub_face.state import Emotion, StateController, shared_controller


@dataclass(slots=True)
class TerminalSidebarSnapshot:
    emotion: str
    note: str
    compact_face: str
    face_lines: list[str]


@dataclass(frozen=True, slots=True)
class TerminalFaceStyle:
    compact_face: str
    face_lines: tuple[str, str, str]


TERMINAL_FACE_STYLES: dict[Emotion, TerminalFaceStyle] = {
    Emotion.NEUTRAL: TerminalFaceStyle(
        compact_face="o==o",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  o==o  |    |  o==o  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.HAPPY: TerminalFaceStyle(
        compact_face="\\^^/",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  \\^^/  |    |  \\^^/  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.SAD: TerminalFaceStyle(
        compact_face="\\~~/",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  \\~~/  |    |  \\~~/  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.ANGRY: TerminalFaceStyle(
        compact_face=">!!<",
        face_lines=(
            "   /--------\\    /--------\\   ",
            "   |  >!!<  |    |  >!!<  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.SURPRISED: TerminalFaceStyle(
        compact_face="(OO)",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  (OO)  |    |  (OO)  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.SLEEPY: TerminalFaceStyle(
        compact_face="-__-",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  -__-  |    |  -__-  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.CURIOUS: TerminalFaceStyle(
        compact_face="o==>",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  o==>  |    |  <==o  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.LOVE: TerminalFaceStyle(
        compact_face="<33>",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  <33>  |    |  <33>  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
    Emotion.THINKING: TerminalFaceStyle(
        compact_face="o..-",
        face_lines=(
            "   .--------.    .--------.   ",
            "   |  o..-  |    |  -..o  |   ",
            "   '--------'    '--------'   ",
        ),
    ),
}


def _face_style(emotion: Emotion) -> TerminalFaceStyle:
    return TERMINAL_FACE_STYLES[emotion]


def _make_sidebar_snapshot(controller: StateController) -> TerminalSidebarSnapshot:
    state = controller.state
    style = _face_style(state.emotion)
    return TerminalSidebarSnapshot(
        emotion=state.emotion.value,
        note=state.note,
        compact_face=style.compact_face,
        face_lines=list(style.face_lines),
    )


class FaceCliRenderer(BubCliRenderer):
    def __init__(
        self,
        console: Console,
        sidebar_provider: Callable[[], TerminalSidebarSnapshot] | None = None,
    ) -> None:
        super().__init__(console)
        self._sidebar_provider = sidebar_provider or self._default_sidebar_snapshot

    def welcome(self, *, model: str, workspace: str) -> None:
        body = (
            f"workspace: {workspace}\n"
            f"model: {model}\n"
            "internal command prefix: ','\n"
            "shell command prefix: ',' at line start (Ctrl-X for shell mode)\n"
            "type ',help' for command list"
        )
        self.console.print(self._integrated_panel(title="Bub", border_style="cyan", text=body))

    def panel(self, kind: MessageKind, text: str) -> RenderableType:
        title, border_style = self._panel_style(kind)
        return self._integrated_panel(title=title, border_style=border_style, text=text)

    def command_output(self, text: str) -> None:
        if not text.strip():
            return
        self.console.print(self.panel("command", text))

    def assistant_output(self, text: str) -> None:
        if not text.strip():
            return
        self.console.print(self.panel("normal", text))

    def error(self, text: str) -> None:
        if not text.strip():
            return
        self.console.print(self.panel("error", text))

    def start_stream(self, kind: MessageKind) -> Live:
        live = Live(
            self.panel(kind, ""),
            console=self.console,
            auto_refresh=False,
            transient=False,
            vertical_overflow="visible",
        )
        live.start()
        live.refresh()
        return live

    def update_stream(self, live: Live, *, kind: MessageKind, text: str) -> None:
        live.update(self.panel(kind, text), refresh=True)

    def finish_stream(self, live: Live, *, kind: MessageKind, text: str) -> None:
        live.update(self.panel(kind, text), refresh=True)
        live.stop()

    def _integrated_panel(self, *, title: str, border_style: str, text: str) -> RenderableType:
        snapshot = self._sidebar_provider()
        status_line = f"emotion:{snapshot.emotion}  note:{snapshot.note}"
        body = Group(
            Text("\n".join(snapshot.face_lines), justify="center"),
            Text(f"{snapshot.compact_face}  {status_line}", justify="center"),
            Text(""),
            Text(text),
        )
        panel_width = self._panel_width()
        panel = Panel(
            body,
            title=title,
            border_style=border_style,
            expand=False,
            width=panel_width,
        )
        return Align.left(panel)

    @staticmethod
    def _default_sidebar_snapshot() -> TerminalSidebarSnapshot:
        return _make_sidebar_snapshot(shared_controller())

    def _panel_width(self) -> int:
        available = max(self.console.size.width - 2, 56)
        return min(available, 92)

    @staticmethod
    def _panel_style(kind: MessageKind) -> tuple[str, str]:
        match kind:
            case "error":
                return "Error", "red"
            case "command":
                return "Command", "green"
            case _:
                return "Bub", "blue"


class FaceAwareCliChannel(BubCliChannel):
    def __init__(self, *args, **kwargs) -> None:
        self._face_controller = shared_controller()
        super().__init__(*args, **kwargs)
        self._renderer = FaceCliRenderer(
            self._renderer.console,
            sidebar_provider=self._build_sidebar_snapshot,
        )

    @contextlib.asynccontextmanager
    async def message_lifespan(self, request_completed):
        self._set_emotion(Emotion.CURIOUS)
        try:
            async with super().message_lifespan(request_completed):
                yield
        except Exception:
            self._set_emotion(Emotion.ANGRY)
            raise

    async def send(self, message: ChannelMessage) -> None:
        self._set_emotion(self._outbound_emotion(message))
        await super().send(message)

    def _render_bottom_toolbar(self) -> FormattedText:
        snapshot = self._build_sidebar_snapshot()
        info = self._last_tape_info
        toolbar = (
            f"{snapshot.compact_face}  "
            f"mood:{snapshot.note}  "
            f"mode:{self._mode}  "
            f"entries:{field_of(info, 'entries', '-')}  "
            f"anchors:{field_of(info, 'anchors', '-')}  "
            f"session:{self._message_template['session_id']}"
        )
        return FormattedText([("", toolbar)])

    def _build_sidebar_snapshot(self) -> TerminalSidebarSnapshot:
        return _make_sidebar_snapshot(self._face_controller)

    def _set_emotion(self, emotion: Emotion) -> None:
        self._face_controller.set_emotion(emotion)

    @staticmethod
    def _outbound_emotion(message: ChannelMessage) -> Emotion:
        if message.kind == "error":
            return Emotion.ANGRY
        if message.kind == "command":
            return Emotion.CURIOUS
        return Emotion.HAPPY


def patch_cli_channel() -> None:
    if cli_module.CliChannel is FaceAwareCliChannel:
        return
    cli_module.CliChannel = FaceAwareCliChannel
