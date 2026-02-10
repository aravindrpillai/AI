from django.urls import path
from django.contrib import admin
from cv.views import CVExtractAPIView

urlpatterns = [
    path('admin/', admin.site.urls),

     path("cv/extract/<str:llm>/", CVExtractAPIView.as_view(), name="cv-extract"),
]
