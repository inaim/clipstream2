#!/usr/bin/env python3
"""
Mobile-to-publish end-to-end harness for ClipStream.

This script simulates the mobile client login, uploads a test video, polls the
backend until SurrealDB reflects the new record, and then runs an MCP-powered
LLM verification pass before persisting the verdict via the new moderation API.

Usage:
    python test/test_e2e_mobile_flow.py \
        --backend http://localhost:8080 \
        --email demo+e2e@example.com \
        --password demo-pass-123

Provide --video to reuse an existing MP4. Otherwise the harness attempts to
generate a short sample clip with ffmpeg.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, Optional

import httpx


def _print(msg: str) -> None:
    """Consistent prefixed logging."""
    print(f"[clipstream-e2e] {msg}")


class MCPClient:
    """Minimal Media Compliance Pipeline client that pulls context from the API."""

    def __init__(self, client: httpx.Client, token: str):
        self.client = client
        self.token = token

    def pull_video_context(self, video_id: str) -> Dict:
        resp = self.client.get(
            f"/api/videos/{video_id}",
            headers=self._auth_headers(),
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}


class LLMVerifier:
    """Heuristic LLM stand-in that can attach to a real model later."""

    def __init__(self, model: str = "heuristic-moderator"):
        self.model = model
        self._flag_terms = {"violence", "gambling", "nsfw", "hate"}

    def evaluate(self, context: Dict) -> Dict[str, object]:
        """Return verdict/summary/confidence akin to an LLM moderation call."""
        title = (context.get("title") or "").lower()
        tags = context.get("hashtags") or []
        body = " ".join(tags + [title])
        hits = sorted(term for term in self._flag_terms if term in body)

        verdict = "approved"
        confidence = 0.86
        summary = "LLM simulation approved the upload."
        metadata: Dict[str, object] = {"model": self.model}

        if hits:
            verdict = "flagged"
            confidence = 0.61
            summary = f"Detected risky keywords: {', '.join(hits)}"
            metadata["flagged_terms"] = hits

        return {
            "verdict": verdict,
            "confidence": confidence,
            "summary": summary,
            "metadata": metadata,
            "mcp_run_id": f"mcp-{uuid.uuid4().hex[:12]}",
        }


class ClipStreamE2EHarness:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.backend = args.backend.rstrip("/")
        self.client = httpx.Client(
            base_url=self.backend,
            timeout=args.http_timeout,
            headers={"User-Agent": "clipstream-mobile-e2e/1.0"},
        )
        self.temp_dir: Optional[str] = None
        self.generated_video: Optional[Path] = None
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.mcp_client: Optional[MCPClient] = None
        self.llm = LLMVerifier(model=args.llm_model)

    def run(self) -> None:
        email = self.args.email or self._generate_email()
        password = self.args.password or "ClipstreamE2E!"
        title = self.args.title or "Mobile MCP Auto Test"

        self.token, self.user_id = self._ensure_account(email, password)
        _print(f"Authenticated as {email} ({self.user_id})")

        video_path = self._prepare_video_file(title)
        upload_result = self._upload_video(video_path, title)
        video_id = upload_result["video_id"]
        _print(f"Upload queued with id={video_id}")

        video_state = self._poll_video_state(video_id)
        _print(f"Video status now '{video_state.get('status')}' (cdn_url={video_state.get('cdn_url')})")

        self.mcp_client = MCPClient(self.client, self.token)
        context = self.mcp_client.pull_video_context(video_id)
        llm_result = self.llm.evaluate(context)
        _print(f"LLM/MCP verdict: {llm_result['verdict']} (confidence={llm_result['confidence']:.2f})")

        persisted = self._persist_llm_verdict(video_id, llm_result)
        _print(f"Verification stored with status '{persisted['status']}'")

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass
        if self.temp_dir and os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _generate_email(self) -> str:
        return f"mobile-e2e+{int(time.time())}@clipstream.dev"

    def _prepare_video_file(self, title: str) -> Path:
        if self.args.video:
            path = Path(self.args.video).expanduser()
            if not path.exists():
                raise FileNotFoundError(f"Video file not found: {path}")
            return path

        self.temp_dir = tempfile.mkdtemp(prefix="clipstream-e2e-")
        sample = Path(self.temp_dir) / "sample.mp4"
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required to auto-generate a sample clip. Provide --video instead.")

        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=steelblue:s=540x960:d=3",
            "-vf",
            "fps=30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(sample),
        ]
        _print(f"Generating sample clip via ffmpeg: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.generated_video = sample
        return sample

    def _ensure_account(self, email: str, password: str) -> tuple[str, str]:
        payload = {"email": email, "password": password, "display_name": "Mobile QA"}
        resp = self.client.post("/api/v1/auth/register", json=payload)
        if resp.status_code == 400:
            resp = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"], data["user_id"]

    def _upload_video(self, video_path: Path, title: str) -> Dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        files = {"file": (video_path.name, video_path.read_bytes(), "video/mp4")}
        data = {"title": title}
        resp = self.client.post("/api/upload", headers=headers, files=files, data=data)
        resp.raise_for_status()
        return resp.json()

    def _poll_video_state(self, video_id: str) -> Dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        deadline = time.time() + self.args.poll_seconds
        last_status = ""
        while time.time() < deadline:
            resp = self.client.get(f"/api/videos/{video_id}", headers=headers)
            if resp.status_code == 404:
                time.sleep(self.args.poll_interval)
                continue
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            if status != last_status:
                _print(f"Video {video_id} status updated to '{status}'")
                last_status = status
            if status in {"active", "processing", "flagged", "blocked"}:
                return data
            time.sleep(self.args.poll_interval)
        raise TimeoutError(f"Video {video_id} did not become ready within {self.args.poll_seconds}s")

    def _persist_llm_verdict(self, video_id: str, llm_result: Dict[str, object]) -> Dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        payload = {
            "verdict": llm_result["verdict"],
            "confidence": llm_result["confidence"],
            "summary": llm_result["summary"],
            "mcp_run_id": llm_result.get("mcp_run_id"),
            "metadata": llm_result.get("metadata", {}),
        }
        resp = self.client.post(f"/api/videos/{video_id}/llm-verification", headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClipStream mobile → upload → MCP verification harness")
    parser.add_argument("--backend", default="http://localhost:8080", help="Backend base URL")
    parser.add_argument("--email", help="Email to register/login (defaults to mobile-e2e+timestamp)")
    parser.add_argument("--password", help="Password to use (defaults to ClipstreamE2E!)")
    parser.add_argument("--video", help="Path to an MP4 file to upload")
    parser.add_argument("--title", help="Override video title")
    parser.add_argument("--poll-seconds", type=int, default=90, help="How long to poll for processing")
    parser.add_argument("--poll-interval", type=float, default=3.0, help="Seconds between poll attempts")
    parser.add_argument("--http-timeout", type=float, default=60.0, help="HTTP client timeout")
    parser.add_argument("--llm-model", default="heuristic-moderator", help="LLM identifier (for metadata only)")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    harness = ClipStreamE2EHarness(args)
    try:
        harness.run()
        _print("End-to-end flow completed successfully ✅")
        return 0
    except Exception as exc:  # noqa: BLE001
        _print(f"❌ Flow failed: {exc}")
        return 1
    finally:
        harness.close()


if __name__ == "__main__":
    sys.exit(main())
