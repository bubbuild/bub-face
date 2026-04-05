from __future__ import annotations

import asyncio
import json
from pathlib import Path

from aiohttp import WSMsgType, web
from aiohttp.typedefs import Handler

from src.bub_face import StateController

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
PORT = 28282  # bubub on 9-keyboard


async def index(_: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC_DIR / "index.html")


async def get_state(request: web.Request) -> web.Response:
    controller: StateController = request.app["controller"]
    return web.json_response(controller.snapshot())


async def set_emotion(request: web.Request) -> web.Response:
    controller: StateController = request.app["controller"]
    payload = await request.json()
    emotion = payload["emotion"]
    state = controller.set_emotion(emotion)
    await broadcast_state(request.app, source="emotion")
    return web.json_response(
        {
            "state": state.to_dict(),
            "display_mode": controller.display_mode.value,
        }
    )


async def patch_state(request: web.Request) -> web.Response:
    controller: StateController = request.app["controller"]
    payload = await request.json()
    state = controller.patch(payload)
    await broadcast_state(request.app, source="patch")
    return web.json_response(
        {
            "state": state.to_dict(),
            "display_mode": controller.display_mode.value,
        }
    )


async def reset_state(request: web.Request) -> web.Response:
    controller: StateController = request.app["controller"]
    state = controller.reset()
    await broadcast_state(request.app, source="reset")
    return web.json_response(
        {
            "state": state.to_dict(),
            "display_mode": controller.display_mode.value,
        }
    )


async def sleep_state(request: web.Request) -> web.Response:
    controller: StateController = request.app["controller"]
    controller.sleep()
    await broadcast_state(request.app, source="sleep")
    return web.json_response(controller.snapshot())


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)

    sockets: set[web.WebSocketResponse] = request.app["sockets"]
    sockets.add(ws)
    await ws.send_json(
        {
            "type": "state",
            "source": "ws_connect",
            **request.app["controller"].snapshot(),
        }
    )

    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue

            payload = json.loads(msg.data)
            action = payload.get("action")
            controller: StateController = request.app["controller"]

            if action == "set_emotion":
                controller.set_emotion(payload["emotion"])
            elif action == "patch":
                controller.patch(payload.get("state", {}))
            elif action == "reset":
                controller.reset()
            elif action == "sleep":
                controller.sleep()
            else:
                await ws.send_json(
                    {"type": "error", "message": f"Unsupported action: {action}"}
                )
                continue

            await broadcast_state(request.app, source="ws")
    finally:
        sockets.discard(ws)

    return ws


async def broadcast_state(app: web.Application, source: str) -> None:
    controller: StateController = app["controller"]
    message = {"type": "state", "source": source, **controller.snapshot()}

    sockets: set[web.WebSocketResponse] = app["sockets"]
    stale: list[web.WebSocketResponse] = []
    for socket in sockets:
        if socket.closed:
            stale.append(socket)
            continue
        await socket.send_json(message)

    for socket in stale:
        sockets.discard(socket)


@web.middleware
async def error_middleware(
    request: web.Request, handler: Handler
) -> web.StreamResponse:
    try:
        return await handler(request)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        return web.json_response({"error": str(exc)}, status=400)


async def on_shutdown(app: web.Application) -> None:
    sockets: set[web.WebSocketResponse] = app["sockets"]
    for socket in set(sockets):
        await socket.close(code=1001, message=b"Server shutdown")
    sockets.clear()


async def on_startup(app: web.Application) -> None:
    async def idle_watchdog() -> None:
        while True:
            await asyncio.sleep(1)
            if app["controller"].maybe_sleep():
                await broadcast_state(app, source="idle_timeout")

    app["idle_watchdog_task"] = asyncio.create_task(idle_watchdog())


async def on_cleanup(app: web.Application) -> None:
    task: asyncio.Task[None] | None = app.get("idle_watchdog_task")
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> web.Application:
    app = web.Application(middlewares=[error_middleware])
    app["controller"] = StateController(idle_timeout_seconds=600)
    app["sockets"] = set()

    app.router.add_get("/", index)
    app.router.add_static("/static/", STATIC_DIR)
    app.router.add_get("/api/state", get_state)
    app.router.add_post("/api/emotion", set_emotion)
    app.router.add_post("/api/state", patch_state)
    app.router.add_post("/api/reset", reset_state)
    app.router.add_post("/api/sleep", sleep_state)
    app.router.add_get("/ws", websocket_handler)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.on_cleanup.append(on_cleanup)
    return app


def main() -> None:
    web.run_app(create_app(), host="127.0.0.1", port=PORT)


async def run() -> None:
    await web._run_app(create_app(), host="127.0.0.1", port=PORT)


if __name__ == "__main__":
    main()
