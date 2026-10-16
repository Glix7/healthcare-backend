from django.urls import path

from .views import MappingListCreateView, PatientMappingView

urlpatterns = [
    path("", MappingListCreateView.as_view(), name="mapping-list-create"),
    path("<int:pk>/", PatientMappingView.as_view(), name="mapping-detail"),
]
