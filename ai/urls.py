from django.urls import path
from django.contrib import admin
from cv.views.cv_upload_api import CVUploadAPIView
from cv.views.cv_search_api import CVSearchAPIView

urlpatterns = [
    path('admin/', admin.site.urls),

     path("cv/candidate/upload/", CVUploadAPIView.as_view(), name="cv-upload"),
     path("cv/candidate/search/", CVSearchAPIView.as_view(), name="cv-search-full"),
     path("cv/candidate/search/<str:id>/", CVSearchAPIView.as_view(), name="cv-search-single"),
]
