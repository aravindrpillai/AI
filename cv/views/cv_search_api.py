from django.db.models import Q
from cv.models import Candidates
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

class CVSearchAPIView(APIView):
 
    def get(self, request, id : str = None):
        try:
            if(id == None):
                skills_param = request.GET.get("skills")
                exp_param = request.GET.get("exp")

                queryset = Candidates.objects.all()
                if skills_param:
                    requested_skills = [
                        s.strip().lower()
                        for s in skills_param.split(",")
                        if s.strip()
                    ]
                    skill_query = Q()
                    for skill in requested_skills:
                        skill_query |= Q(skills__icontains=skill)
                    queryset = queryset.filter(skill_query)
                else:
                    raise Exception("Filters required")

                resp = [c.show() for c in queryset]
                return Response(resp, status=status.HTTP_200_OK)
            else:
                candidate = Candidates.objects.get(id=int(id))
                return Response(candidate.show(), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Extraction failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
