from __future__ import annotations

import uuid, traceback
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from claims.services import ClaimService
from claims.utils import save_uploaded_file


class ClaimsFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, conv_id: uuid.UUID):
        try:
            conv = ClaimService.get_conversation(conv_id)
            if not conv:
                return Response(
                    {"error": "conversation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            if conv.submitted:
                return Response(
                    {"error": "conversation already submitted"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file = request.FILES.get("file")
            if not file:
                return Response(
                    {"error": "file is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            caption = (request.data.get("caption") or "").strip() or None

            # ── Save + convert if needed ───────────────────────────────────
            actual_uuid, final_filename, final_mime, _ = save_uploaded_file(file)

            # ── Persist to DB ──────────────────────────────────────────────
            ClaimService.save_file_message(
                conv,
                file_id=actual_uuid,
                filename=final_filename,
                content_type=final_mime,
                message=caption,
                provider_file_id=None,
            )

            print(f"[Upload] file={final_filename} mime={final_mime} uuid={actual_uuid}")

            return Response({
                "file_uid":     str(actual_uuid),
                "filename":     final_filename,
                "content_type": final_mime,
                "size":         file.size,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("===ERROR upload:\n", traceback.format_exc())
            return Response(
                {"error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )