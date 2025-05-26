from django import forms
from .models import PatientPrediction

class UploadForm(forms.ModelForm):
    class Meta:
        model  = PatientPrediction
        fields = ("data_file",)
