from __future__ import annotations

import os, mimetypes, anthropic
from ai.constants import MAX_TOKEN
from aiengine.agents.base import AgentAbstract
from typing import List, Optional, Dict, Any
from aiengine.types import LocalFile, UploadedRef


CLAUDE_SUPPORTED_IMAGES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
CLAUDE_SUPPORTED_DOCS   = {"application/pdf", "text/plain", "text/csv", "text/html", "text/xml"}


class ClaudeAdapter(AgentAbstract):
    provider = "claude"

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    @staticmethod
    def _resolve_filename(f: LocalFile) -> str:
        return f.filename or os.path.basename(f.path)

    @staticmethod
    def _resolve_mime(f: LocalFile) -> str:
        if f.mime_type:
            return f.mime_type
        mt, _ = mimetypes.guess_type(f.path)
        return mt or "application/octet-stream"

    def upload_files(self, files: List[LocalFile]) -> List[UploadedRef]:
        out: List[UploadedRef] = []
        for f in files:
            res = self.client.beta.files.upload(
                file=(self._resolve_filename(f), open(f.path, "rb"), self._resolve_mime(f)),
            )
            out.append(UploadedRef(
                provider="claude",
                file_id=res.id,
                filename=self._resolve_filename(f),
                mime_type=self._resolve_mime(f),
            ))
        return out

    def push_message(
        self,
        *,
        model: str,
        system_prompt: Optional[str],
        payload: Dict[str, Any],
        uploads: Optional[List[UploadedRef]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        conversation     = payload.get("conversation", [])
        current_state    = payload.get("current_state", {})
        extra_instruction = payload.get("instruction", "")

        messages = []

        # All turns except the last go in as plain role/content
        for turn in conversation[:-1]:
            messages.append({
                "role":    turn["role"],
                "content": turn["content"],
            })

        # Last user turn — attach files + state + instruction
        last_turn = conversation[-1] if conversation else {"role": "user", "content": ""}

        blocks: List[Dict[str, Any]] = [
            {"type": "text", "text": last_turn["content"]},
            {"type": "text", "text": f"\n\nCurrent FNOL state:\n{current_state}"},
        ]

        if extra_instruction:
            blocks.append({"type": "text", "text": f"\n\n{extra_instruction}"})

        unsupported_files: List[str] = []

        for u in (uploads or []):
            if u.provider != "claude":
                continue

            mime = (u.mime_type or "").lower()

            if mime in CLAUDE_SUPPORTED_IMAGES:
                blocks.append({
                    "type": "image",
                    "source": {"type": "file", "file_id": u.file_id},
                })
            elif mime in CLAUDE_SUPPORTED_DOCS:
                blocks.append({
                    "type": "document",
                    "source": {"type": "file", "file_id": u.file_id},
                    "title": u.filename,
                })
            else:
                unsupported_files.append(f"{u.filename} ({mime or 'unknown type'})")

        if unsupported_files:
            blocks.append({
                "type": "text",
                "text": (
                    f"\n\nNote: The following files were uploaded but cannot be rendered inline: "
                    f"{', '.join(unsupported_files)}. Acknowledge them in your analysis."
                ),
            })

        messages.append({"role": "user", "content": blocks})

        # ── Enforce JSON via system prompt injection ───────────────────────
        # Prefill not supported on this model — append JSON reminder to system
        json_enforcement = (
            "\n\nCRITICAL INSTRUCTION: You MUST respond with valid JSON only. "
            "No plain text. No markdown. No code fences. No preamble. "
            "Your entire response must be a single valid JSON object starting with { and ending with }."
        )
        final_system = (system_prompt or "") + json_enforcement

        params: Dict[str, Any] = {
            "model":      model,
            "max_tokens": MAX_TOKEN,
            "messages":   messages,
            "betas":      ["files-api-2025-04-14"],
            "system":     final_system,
        }
        if extra:
            params.update(extra)

        resp = self.client.beta.messages.create(**params)

        text_parts = [
            getattr(block, "text", "")
            for block in (getattr(resp, "content", []) or [])
            if getattr(block, "type", None) == "text"
        ]

        return {"text": "\n".join(text_parts).strip(), "raw": resp}