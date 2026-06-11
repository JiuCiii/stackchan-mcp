from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from . import audio_processing
from .audio_server import audio_url, start_audio_server
from .stackchan_client import StackchanClient
from .stackchan_config import StackchanConfig, load_config

logger = logging.getLogger(__name__)

FACE_MAP = {
    "neutral": "calm",
    "happy": "happy",
    "shy": "shy",
    "angry": "pouty",
    "sad": "sleepy",
    "surprised": "happy",
    "thinking": "thinking",
    "sleepy": "sleepy",
}


@dataclass(frozen=True)
class QueueConfig:
    base_url: str
    token: str
    device_id: str
    poll_seconds: float
    heartbeat_seconds: float


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"'")
        if name:
            os.environ.setdefault(name, value)


def load_queue_config() -> QueueConfig:
    token = os.environ.get("STACKCHAN_DEVICE_TOKEN", "").strip()
    if not token:
        raise ValueError("STACKCHAN_DEVICE_TOKEN is required")
    return QueueConfig(
        base_url=os.environ.get(
            "XIAOKE_ACTIONS_BASE_URL",
            "https://xiaoke-actions.onrender.com",
        ).rstrip("/"),
        token=token,
        device_id=os.environ.get("STACKCHAN_DEVICE_ID", "stackchan-01").strip(),
        poll_seconds=max(0.2, float(os.environ.get("STACKCHAN_POLL_SECONDS", "1.5"))),
        heartbeat_seconds=max(
            5.0,
            float(os.environ.get("STACKCHAN_HEARTBEAT_SECONDS", "30")),
        ),
    )


class QueueClient:
    def __init__(self, config: QueueConfig):
        self.config = config

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.token}",
            "X-Stackchan-Device": self.config.device_id,
            "Accept": "application/json",
        }

    def poll(self) -> dict[str, Any] | None:
        response = requests.get(
            f"{self.config.base_url}/stackchan/poll",
            headers=self.headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("command")

    def report(self, command_id: str, *, result: dict | None = None, error: str | None = None) -> None:
        body: dict[str, Any] = {"id": command_id, "ok": error is None}
        if error is None:
            body["result"] = result or {}
        else:
            body["error"] = error[:500]
        response = requests.post(
            f"{self.config.base_url}/stackchan/result",
            headers={**self.headers, "Content-Type": "application/json"},
            json=body,
            timeout=20,
        )
        response.raise_for_status()

    def heartbeat(self, status: dict[str, Any]) -> None:
        response = requests.post(
            f"{self.config.base_url}/stackchan/heartbeat",
            headers={**self.headers, "Content-Type": "application/json"},
            json={
                "device_id": self.config.device_id,
                "firmware_version": "stackchan-mcp-http-bridge-1",
                **status,
            },
            timeout=20,
        )
        response.raise_for_status()


class CommandExecutor:
    def __init__(self, client: StackchanClient, config: StackchanConfig):
        self.client = client
        self.config = config

    def status(self, current_action: str | None = None) -> dict[str, Any]:
        playback = self.client.playback_status()
        return {
            "current_action": current_action,
            "device_online": True,
            "free_heap": playback.get("free_heap"),
            "free_psram": playback.get("free_psram"),
            "playing": playback.get("playing"),
            "servo_ready": playback.get("servo_ready"),
        }

    def execute(self, command: dict[str, Any]) -> dict[str, Any]:
        action = str(command.get("action") or "")
        payload = command.get("payload") or {}
        if action == "speak":
            return self._speak(str(payload.get("text") or ""))
        if action == "emote":
            expression = str(payload.get("expression") or "").lower()
            face = FACE_MAP.get(expression)
            if not face:
                raise ValueError(f"unsupported_expression:{expression}")
            return self._require_success(self.client.set_face(face), face=face)
        if action == "move_head":
            yaw = float(payload.get("yaw", 0))
            pitch = float(payload.get("pitch", 0))
            return self._require_success(
                self.client.move(yaw, max(5.0, min(85.0, 45.0 + pitch)), 50),
                yaw=yaw,
                pitch=pitch,
            )
        if action == "wiggle":
            return self._require_success(self.client.gesture("shake"), gesture="shake")
        raise ValueError(f"unsupported_action:{action}")

    def _speak(self, text: str) -> dict[str, Any]:
        if not text.strip():
            raise ValueError("text_required")
        wav_path = audio_processing.generate_tts(text, "zh", self.config)
        audio_processing.validate_playback_wav(wav_path)
        result = self.client.play(
            audio_url(self.config.mac_ip, self.config.audio_serve_port, wav_path.name)
        )
        return self._require_success(result, text_length=len(text), audio=wav_path.name)

    @staticmethod
    def _require_success(result: dict[str, Any], **details: Any) -> dict[str, Any]:
        if not result.get("success"):
            raise RuntimeError(f"device_command_failed:{json.dumps(result, ensure_ascii=False)}")
        return {**details, "device": result}


def run_bridge(
    queue: QueueClient,
    executor: CommandExecutor,
    queue_config: QueueConfig,
    *,
    once: bool = False,
) -> None:
    start_audio_server(executor.config.audio_serve_port)
    last_heartbeat = 0.0
    while True:
        now = time.monotonic()
        if now - last_heartbeat >= queue_config.heartbeat_seconds:
            try:
                queue.heartbeat(executor.status())
                last_heartbeat = now
            except Exception:
                logger.exception("Stack-chan heartbeat failed")

        try:
            command = queue.poll()
        except Exception:
            logger.exception("Stack-chan queue poll failed")
            if once:
                raise
            time.sleep(queue_config.poll_seconds)
            continue

        if command:
            command_id = str(command.get("id") or "")
            try:
                result = executor.execute(command)
                queue.report(command_id, result=result)
                logger.info("Completed Stack-chan command %s", command_id)
            except Exception as exc:
                logger.exception("Stack-chan command %s failed", command_id)
                queue.report(command_id, error=str(exc))

        if once:
            return
        time.sleep(queue_config.poll_seconds)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_env_file(repo_root / ".env")
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    queue_config = load_queue_config()
    device_config = load_config()
    run_bridge(
        QueueClient(queue_config),
        CommandExecutor(StackchanClient(device_config), device_config),
        queue_config,
        once="--once" in os.sys.argv,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
