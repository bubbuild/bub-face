from bub_face.state import Emotion, StateController


def test_set_emotion_uses_preset() -> None:
    controller = StateController()

    state = controller.set_emotion(Emotion.HAPPY)

    assert state.emotion is Emotion.HAPPY
    assert state.accent == "#ffd166"
    assert state.note == "Delighted"


def test_patch_clamps_runtime_values() -> None:
    controller = StateController()

    state = controller.patch(
        {
            "emotion": "angry",
            "openness": 10,
            "pupil_x": 5,
            "pupil_y": -3,
            "blink_interval": 0.1,
        }
    )

    assert state.emotion is Emotion.ANGRY
    assert state.openness == 1.0
    assert state.pupil_x == 1.0
    assert state.pupil_y == -1.0
    assert state.blink_interval == 1.2


def test_reset_returns_neutral_state() -> None:
    controller = StateController()
    controller.set_emotion("sad")

    state = controller.reset()

    assert state.emotion is Emotion.NEUTRAL
    assert state.note == "Idle"


def test_maybe_sleep_switches_to_clock_mode_after_timeout() -> None:
    now = 0.0

    def fake_time() -> float:
        return now

    controller = StateController(idle_timeout_seconds=600, time_fn=fake_time)

    now = 601.0

    assert controller.maybe_sleep() is True
    assert controller.snapshot()["display_mode"] == "clock"


def test_wake_restores_face_mode_and_refreshes_timer() -> None:
    now = 0.0

    def fake_time() -> float:
        return now

    controller = StateController(idle_timeout_seconds=600, time_fn=fake_time)
    now = 700.0
    controller.maybe_sleep()

    assert controller.snapshot()["display_mode"] == "clock"

    now = 701.0
    assert controller.wake() is True
    assert controller.snapshot()["display_mode"] == "face"

    now = 1000.0
    assert controller.maybe_sleep() is False


def test_sleep_switches_immediately_to_clock_mode() -> None:
    controller = StateController()

    changed = controller.sleep()

    assert changed is True
    assert controller.snapshot()["display_mode"] == "clock"
    assert controller.sleep() is False
