import asyncio

from bub import hookimpl
from bub.channels import Channel
from bub.types import MessageHandler
from loguru import logger


class FaceChannel(Channel):
    def __init__(self) -> None:
        self._ongoing_task: asyncio.Task[None] | None = None

    async def start(self, stop_event: asyncio.Event) -> None:
        from src.bub_face.server import run

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


@hookimpl
def provide_channels(message_handler: MessageHandler) -> list[Channel]:
    _ = message_handler  # not used
    return [FaceChannel()]
