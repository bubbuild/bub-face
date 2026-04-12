import asyncio

from bub.channels.message import ChannelMessage
from rich.console import Console

from bub_face.state import Emotion, shared_controller
from bub_face.terminal import (
    BubCliChannel,
    FaceAwareCliChannel,
    FaceCliRenderer,
    TerminalSidebarSnapshot,
    _face_style,
)


def test_renderer_panel_includes_face_sidebar() -> None:
    console = Console(record=True, width=140)
    renderer = FaceCliRenderer(
        console,
        sidebar_provider=lambda: TerminalSidebarSnapshot(
            emotion="thinking",
            note="Reasoning",
            compact_face="o..-",
            face_lines=[
                "   .--------.    .--------.   ",
                "   |  o..-  |    |  -..o  |   ",
                "   '--------'    '--------'   ",
            ],
        ),
    )

    console.print(renderer.panel("normal", "hello from bub"))
    output = console.export_text()

    assert "Bub" in output
    assert "emotion:thinking" in output
    assert "workspace:bubbuild" not in output
    assert ".--------." in output
    assert "o..-" in output
    assert "hello from bub" in output


def test_send_updates_emotion_via_legacy_cli_outbound(monkeypatch) -> None:
    channel = object.__new__(FaceAwareCliChannel)
    controller = shared_controller()
    controller.reset()
    channel._face_controller = controller

    captured: list[str] = []

    async def fake_send(self, message: ChannelMessage) -> None:
        captured.append(message.content)

    monkeypatch.setattr(BubCliChannel, "send", fake_send)

    asyncio.run(
        FaceAwareCliChannel.send(
            channel,
            ChannelMessage(
                session_id="cli_session",
                channel="cli",
                chat_id="local",
                content="hello",
                kind="normal",
            ),
        )
    )

    assert captured == ["hello"]
    assert controller.state.emotion is Emotion.HAPPY


def test_terminal_face_changes_with_emotion() -> None:
    neutral = _face_style(Emotion.NEUTRAL)
    happy = _face_style(Emotion.HAPPY)
    angry = _face_style(Emotion.ANGRY)

    assert neutral != happy
    assert happy != angry
    assert neutral.compact_face == "o==o"
    assert happy.compact_face == "\\^^/"
    assert angry.compact_face == ">!!<"
