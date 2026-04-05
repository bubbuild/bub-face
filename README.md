# bub-face

`bub-face` is a `bub` plugin that provides a web-based robot eyes UI backed by `aiohttp` and registers the `face` channel through the `bub` plugin entry point.

## Demo

https://github.com/user-attachments/assets/4e0baa87-4e93-4d39-8416-1a8db84af99f

## Demo Limitation

This Web UI requires the display to stay active and visible. It is intended for demo and presentation use only, not for production scenarios where the screen may sleep, turn off, or run unattended.

If you want a longer-running physical setup, use a dedicated low-power display device instead of a general-purpose monitor.

## Installation

Install this plugin into the same Python environment as `bub`.

```bash
uv pip install git+https://github.com/bubbuild/bub-face.git
```


## Behavior

- The screen shows the robot face by default.
- After 10 minutes of inactivity, the UI switches to a full-screen date/time clock.
- `POST /api/sleep` switches the UI to `clock` immediately.
- Any `GET /api/state` request wakes the screen and switches it back to `face`.
- Emotion changes, state patches, resets, and WebSocket control messages also count as activity.

## Local Run

If you want to debug the web UI provided by this plugin on its own, you can start the bundled server directly:

```bash
python -m bub_face.server
```

Then open `http://127.0.0.1:28282`.

## API

```bash
curl http://127.0.0.1:28282/api/state

curl -X POST http://127.0.0.1:28282/api/emotion \
  -H 'Content-Type: application/json' \
  -d '{"emotion":"happy"}'

curl -X POST http://127.0.0.1:28282/api/state \
  -H 'Content-Type: application/json' \
  -d '{"pupil_x":0.35,"pupil_y":-0.2,"openness":0.85}'

curl -X POST http://127.0.0.1:28282/api/sleep
```

WebSocket clients can connect to `/ws` and send:

```json
{"action":"set_emotion","emotion":"curious"}
{"action":"patch","state":{"pupil_x":-0.5,"pupil_y":0.2}}
{"action":"reset"}
{"action":"sleep"}
```

`GET /api/state` and WebSocket `state` events include:

```json
{
  "display_mode": "face",
  "idle_timeout_seconds": 600
}
```

Supported emotions:

- `neutral`
- `happy`
- `sad`
- `angry`
- `surprised`
- `sleepy`
- `curious`
- `love`
- `thinking`
