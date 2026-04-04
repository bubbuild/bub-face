# Web Robo Eyes

A web-based robo eyes demo with an `aiohttp` backend and multiple emotional presets.

## Behavior

- The screen shows the face by default.
- After 10 minutes without activity, the UI switches to a full-screen date/time clock.
- `POST /api/sleep` switches the UI to `clock` immediately.
- Any `GET /api/state` request wakes the screen and switches it back to `face`.
- Emotion changes, patches, resets, and WebSocket control messages also count as activity.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m bub_face.server
```

Open `http://127.0.0.1:28282`.

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

`GET /api/state` and WebSocket `state` events now include:

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
