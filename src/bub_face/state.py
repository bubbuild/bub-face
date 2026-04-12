from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from enum import StrEnum
from time import monotonic
from typing import Any, Callable


class Emotion(StrEnum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    SLEEPY = "sleepy"
    CURIOUS = "curious"
    LOVE = "love"
    THINKING = "thinking"


class DisplayMode(StrEnum):
    FACE = "face"
    CLOCK = "clock"


@dataclass(slots=True)
class EyeState:
    emotion: Emotion = Emotion.NEUTRAL
    openness: float = 1.0
    pupil_size: float = 0.38
    pupil_x: float = 0.0
    pupil_y: float = 0.0
    brow_tilt: float = 0.0
    eyelid_curve: float = 0.0
    glow: float = 0.45
    blink_interval: float = 3.8
    accent: str = "#53f2c7"
    background: str = "radial-gradient(circle at top, #15273d 0%, #05070c 72%)"
    spark: str = "#c7fff2"
    note: str = "Idle"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["emotion"] = self.emotion.value
        return payload


EMOTION_PRESETS: dict[Emotion, dict[str, Any]] = {
    Emotion.NEUTRAL: {
        "openness": 1.0,
        "pupil_size": 0.38,
        "brow_tilt": 0.0,
        "eyelid_curve": 0.05,
        "glow": 0.45,
        "blink_interval": 3.8,
        "accent": "#53f2c7",
        "background": "radial-gradient(circle at top, #15273d 0%, #05070c 72%)",
        "spark": "#c7fff2",
        "note": "Idle",
    },
    Emotion.HAPPY: {
        "openness": 0.82,
        "pupil_size": 0.34,
        "brow_tilt": -0.18,
        "eyelid_curve": 0.34,
        "glow": 0.7,
        "blink_interval": 2.8,
        "accent": "#ffd166",
        "background": "radial-gradient(circle at top, #54351a 0%, #0b0f18 78%)",
        "spark": "#fff2c2",
        "note": "Delighted",
    },
    Emotion.SAD: {
        "openness": 0.62,
        "pupil_size": 0.36,
        "brow_tilt": 0.2,
        "eyelid_curve": -0.22,
        "glow": 0.3,
        "blink_interval": 5.2,
        "accent": "#76b7ff",
        "background": "radial-gradient(circle at top, #102742 0%, #05070c 78%)",
        "spark": "#c6e1ff",
        "note": "Low energy",
    },
    Emotion.ANGRY: {
        "openness": 0.72,
        "pupil_size": 0.3,
        "brow_tilt": 0.42,
        "eyelid_curve": -0.1,
        "glow": 0.78,
        "blink_interval": 2.3,
        "accent": "#ff5c5c",
        "background": "radial-gradient(circle at top, #421111 0%, #09040a 78%)",
        "spark": "#ffd0d0",
        "note": "Locked on target",
    },
    Emotion.SURPRISED: {
        "openness": 1.0,
        "pupil_size": 0.26,
        "brow_tilt": -0.28,
        "eyelid_curve": 0.02,
        "glow": 0.88,
        "blink_interval": 4.6,
        "accent": "#f8f272",
        "background": "radial-gradient(circle at top, #4f4c1e 0%, #08090d 78%)",
        "spark": "#fff8c4",
        "note": "Unexpected input",
    },
    Emotion.SLEEPY: {
        "openness": 0.34,
        "pupil_size": 0.42,
        "brow_tilt": 0.08,
        "eyelid_curve": -0.28,
        "glow": 0.24,
        "blink_interval": 1.8,
        "accent": "#b298ff",
        "background": "radial-gradient(circle at top, #251b44 0%, #06050c 78%)",
        "spark": "#ddd3ff",
        "note": "Power saving",
    },
    Emotion.CURIOUS: {
        "openness": 0.94,
        "pupil_size": 0.33,
        "brow_tilt": -0.08,
        "eyelid_curve": 0.12,
        "glow": 0.6,
        "blink_interval": 3.1,
        "accent": "#56c4ff",
        "background": "radial-gradient(circle at top, #0f2f47 0%, #05070c 78%)",
        "spark": "#cbf0ff",
        "note": "Inspecting",
    },
    Emotion.LOVE: {
        "openness": 0.86,
        "pupil_size": 0.28,
        "brow_tilt": -0.22,
        "eyelid_curve": 0.28,
        "glow": 0.82,
        "blink_interval": 2.6,
        "accent": "#ff6fae",
        "background": "radial-gradient(circle at top, #481d31 0%, #09050c 78%)",
        "spark": "#ffd4e4",
        "note": "Affection lock",
    },
    Emotion.THINKING: {
        "openness": 0.78,
        "pupil_size": 0.32,
        "brow_tilt": 0.12,
        "eyelid_curve": 0.0,
        "glow": 0.52,
        "blink_interval": 4.3,
        "accent": "#8fffa9",
        "background": "radial-gradient(circle at top, #1e3821 0%, #05070c 78%)",
        "spark": "#d9ffe2",
        "note": "Reasoning",
    },
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


class StateController:
    def __init__(
        self,
        *,
        idle_timeout_seconds: int = 600,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self._state = self._preset(Emotion.NEUTRAL)
        self._field_names = {field.name for field in fields(EyeState)}
        self._idle_timeout_seconds = idle_timeout_seconds
        self._time_fn = time_fn or monotonic
        self._display_mode = DisplayMode.FACE
        self._last_active_at = self._time_fn()
        self._listeners: list[Callable[[], None]] = []

    def add_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.remove(callback)

    def _notify(self) -> None:
        for listener in self._listeners:
            listener()

    @property
    def state(self) -> EyeState:
        return self._state

    @property
    def display_mode(self) -> DisplayMode:
        return self._display_mode

    @property
    def idle_timeout_seconds(self) -> int:
        return self._idle_timeout_seconds

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self._state.to_dict(),
            "emotions": self.list_emotions(),
            "display_mode": self._display_mode.value,
            "idle_timeout_seconds": self._idle_timeout_seconds,
        }

    def reset(self) -> EyeState:
        self.wake()
        self._state = self._preset(Emotion.NEUTRAL)
        self._notify()
        return self._state

    def set_emotion(self, emotion: str | Emotion) -> EyeState:
        self.wake()
        parsed = emotion if isinstance(emotion, Emotion) else Emotion(emotion)
        self._state = self._preset(parsed)
        self._notify()
        return self._state

    def patch(self, payload: dict[str, Any]) -> EyeState:
        self.wake()
        current = self._state.to_dict()
        emotion = payload.get("emotion", current["emotion"])
        next_state = self._preset(Emotion(emotion))

        merged = {**next_state.to_dict(), **payload}
        filtered = {
            key: value
            for key, value in merged.items()
            if key in self._field_names and value is not None
        }
        filtered["emotion"] = Emotion(filtered["emotion"])

        for key in ("openness", "pupil_size", "glow"):
            if key in filtered:
                filtered[key] = _clamp(float(filtered[key]), 0.0, 1.0)
        for key in ("pupil_x", "pupil_y", "brow_tilt", "eyelid_curve"):
            if key in filtered:
                filtered[key] = _clamp(float(filtered[key]), -1.0, 1.0)
        if "blink_interval" in filtered:
            filtered["blink_interval"] = _clamp(
                float(filtered["blink_interval"]), 1.2, 8.0
            )

        self._state = EyeState(**filtered)
        self._notify()
        return self._state

    def list_emotions(self) -> list[str]:
        return [emotion.value for emotion in Emotion]

    def wake(self) -> bool:
        self._last_active_at = self._time_fn()
        if self._display_mode is DisplayMode.FACE:
            return False
        self._display_mode = DisplayMode.FACE
        return True

    def sleep(self) -> bool:
        if self._display_mode is DisplayMode.CLOCK:
            return False
        self._display_mode = DisplayMode.CLOCK
        self._notify()
        return True

    def maybe_sleep(self) -> bool:
        if self._display_mode is DisplayMode.CLOCK:
            return False
        if self._time_fn() - self._last_active_at < self._idle_timeout_seconds:
            return False
        return self.sleep()

    def _preset(self, emotion: Emotion) -> EyeState:
        return EyeState(emotion=emotion, **EMOTION_PRESETS[emotion])


DEFAULT_IDLE_TIMEOUT_SECONDS = 600
_shared_controller: StateController | None = None


def shared_controller() -> StateController:
    global _shared_controller
    if _shared_controller is None:
        _shared_controller = StateController(
            idle_timeout_seconds=DEFAULT_IDLE_TIMEOUT_SECONDS
        )
    return _shared_controller
