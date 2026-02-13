import base64, os, uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cv.models import Candidates
from cv.doc_reader import read_document_text
from cv.llm.factory import get_extractor


class CVUploadAPIView(APIView):
    
    def post(self, request):
        filename = (request.data.get("filename") or "").strip()
        file_b64 = request.data.get("file_base64")
        llm_model = (request.data.get("llm_model") or "").strip()
        passkey = (request.data.get("passkey") or "").strip()

        if not filename or not file_b64 or not llm_model:
            return Response(
                {"error": "filename, file_base64, and llm_model are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Decode base64 (support data URL too)
        try:
            if isinstance(file_b64, str) and "," in file_b64 and file_b64.strip().lower().startswith("data:"):
                file_b64 = file_b64.split(",", 1)[1]
            file_bytes = base64.b64decode(file_b64, validate=True)
        except Exception:
            return Response({"error": "Invalid base64 content"}, status=status.HTTP_400_BAD_REQUEST)

        # 3) Save to disk under STATIC_ROOT/uploads/cv/
        rel_dir = os.path.join("uploads", "cv")
        abs_dir = os.path.join(settings.STATIC_ROOT, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)

        # Keep original extension, but avoid collisions
        _, ext = os.path.splitext(filename)
        safe_name = f"{uuid.uuid4()}{ext or ''}"
        abs_path = os.path.join(abs_dir, safe_name)
        rel_path = os.path.join(rel_dir, safe_name).replace("\\", "/")

        with open(abs_path, "wb") as f:
            f.write(file_bytes)

        print("==>", safe_name, abs_path, rel_path)
        # Store to DB
        candidate = Candidates.create_record(fileid=safe_name, filename=filename)
        
        extracted_text = read_document_text(abs_path)
        if not extracted_text.strip():
            raise Exception("No extractable text found in document.")
        payload = get_extractor(llm_model).extract(extracted_text)
        
        candidate = Candidates.update_with_llm_json(candidate=candidate, llm=llm_model, payload_json=payload)  
        resp = {
            "candidate_id" : candidate.id
        }
        return Response(resp, status=status.HTTP_201_CREATED)

        
    