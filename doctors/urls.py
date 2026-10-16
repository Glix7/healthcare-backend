from django.urls import path

from .views import DoctorDetailView, DoctorListCreateView

urlpatterns = [
    path("", DoctorListCreateView.as_view(), name="doctor-list-create"),
    path("<int:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
]
