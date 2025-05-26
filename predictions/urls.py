from django.urls import path
from . import views
urlpatterns = [
    path("", views.upload_and_predict, name="upload"),
    path("result/<int:pk>/", views.prediction_detail, name="prediction-detail"),
]

