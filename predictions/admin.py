from django.contrib import admin
from .models import PatientPrediction

@admin.register(PatientPrediction)
class PatientPredictionAdmin(admin.ModelAdmin):
    list_display = ("user", "result", "probability", "uploaded_at")
    list_filter  = ("result", "uploaded_at")
    search_fields = ("user__username",)
