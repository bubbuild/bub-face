import asyncio

from bub import hookimpl
from bub.channels import Channel
from bub.envelope import field_of
from bub.types import Envelope, MessageHandler, State
from loguru import logger

from bub_face.state import Emotion, shared_controller


class FaceChannel(Channel):
    name = "face"

    def __init__(self) -> None:
        self._ongoing_task: asyncio.Task[None] | None = None

    async def start(self, stop_event: asyncio.Event) -> None:
        from bub_face.server import run

        logger.info("channel.face starting")
        self._ongoing_task = asyncio.create_task(run())

    async def stop(self) -> None:
        if self._ongoing_task is not None:
            logger.info("channel.face stopping")
            self._ongoing_task.cancel()
            try:
                await self._ongoing_task
            except asyncio.CancelledError:
                pass
            self._ongoing_task = None


@hookimpl(tryfirst=True)
def provide_channels(message_handler: MessageHandler) -> list[Channel]:
    _ = message_handler  # not used
    from bub_face.terminal import patch_cli_channel

    patch_cli_channel()
    return [FaceChannel()]


@hookimpl
async def load_state(message: Envelope, session_id: str) -> State:
    _ = session_id  # not used
    channel = field_of(message, "channel")
    if channel == "xiaoai":
        shared_controller().set_emotion(Emotion.NEUTRAL)
    return {}
