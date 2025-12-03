from django import forms
from .models import PatientPrediction

# Changed to match what the model expects: M/F single letters
GENDER_CHOICES = [
    ("", "---"),  # Empty option
    ("M", "Male"),
    ("F", "Female")
]

class ManualPredictForm(forms.Form):
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    bmi = forms.FloatField(required=False)
    Omega3_Index = forms.FloatField(required=False)
    Hand_Grip = forms.FloatField(required=False)
    rs174537 = forms.CharField(required=False, max_length=10)   # categorical SNP
    rs174626 = forms.CharField(required=False, max_length=10)   # categorical SNP
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