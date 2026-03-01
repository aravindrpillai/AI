from __future__ import annotations
import os
from django.conf import settings
from aiengine import AIAgentHandler, LocalFile, UploadedRef
from claims.services import ClaimService

TMP_DIR  = os.path.join(settings.BASE_DIR, "tmp")
PROVIDER = "claude"
MODEL    = "claude-sonnet-4-6"


def get_handler(prompt: str) -> AIAgentHandler:
    return AIAgentHandler(provider=PROVIDER, model=MODEL, system_prompt=prompt)


def resolve_uploads(handler: AIAgentHandler, file_messages: list) -> list[UploadedRef]:
    """
    For each file message:
    - provider_file_id exists → reuse, no re-upload
    - not exists → upload now, persist provider_file_id to DB
    """
    uploads = []
    for fm in file_messages:
        if fm.provider_file_id:
            uploads.append(UploadedRef(
                provider=PROVIDER,
                file_id=fm.provider_file_id,
                filename=fm.filename,
                mime_type=fm.content_type,
            ))
        else:
            local_path = os.path.join(TMP_DIR, str(fm.file_id))
            if not os.path.exists(local_path):
                print(f"[AI] File missing on disk, skipping: {local_path}")
                continue
            refs = handler.upload_files([
                LocalFile(local_path, filename=fm.filename, mime_type=fm.content_type)
            ])
            if refs:
                ClaimService.update_provider_file_id(fm.file_id, refs[0].file_id)
                uploads.append(refs[0])
    return uploads


def log_claude_response(resp: dict) -> None:
    raw_resp = resp.get("raw")
    if raw_resp:
        stop_reason = getattr(raw_resp, "stop_reason", "unknown")
        usage       = getattr(raw_resp, "usage", None)
        print(
            f"[Claude] stop_reason={stop_reason} "
            f"input_tokens={getattr(usage, 'input_tokens', '?')} "
            f"output_tokens={getattr(usage, 'output_tokens', '?')}"
        )