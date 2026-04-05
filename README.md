# bub-face

`bub-face` is a `bub` plugin that provides a web-based robot eyes UI backed by `aiohttp` and registers the `face` channel through the `bub` plugin entry point.

## Demo

<video src="docs/assets/demo.mp4" controls muted playsinline width="960"></video>

[Download the 10-second demo video](docs/assets/demo.mp4)

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
