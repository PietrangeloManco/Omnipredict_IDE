from django import forms
from .models import PatientPrediction

GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("other", "Other")]

class ManualPredictForm(forms.Form):
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    bmi = forms.FloatField(required=False)
    Omega3_Index = forms.FloatField(required=False)
    Hand_Grip = forms.FloatField(required=False)
    rs174537 = forms.CharField(required=False)   # categorical SNP
    rs174626 = forms.CharField(required=False)   # categorical SNP
    SCAT = forms.FloatField(required=False)

class UploadForm(forms.ModelForm):
    already_preprocessed = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Tick if your file is already preprocessed for the model."
    )
    class Meta:
        model = PatientPrediction
        fields = ["data_file"]
