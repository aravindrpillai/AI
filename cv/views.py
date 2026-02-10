from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from cv.doc_reader import read_document_text
from cv.llm.factory import get_extractor

class CVExtractAPIView(APIView):
 
    def get(self, request, llm):
        
        path = "C:/aravind/aravindrpillai/cvs/Vanaroja.docx"

        try:
            text = read_document_text(path)
            if not text.strip():
                return Response({"error": "No extractable text found in document."}, status=status.HTTP_400_BAD_REQUEST)
            data = get_extractor(llm).extract(text)
            return Response(data, status=status.HTTP_200_OK)

        except FileNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # don’t leak internals in prod; log it instead
            return Response({"error": f"Extraction failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
