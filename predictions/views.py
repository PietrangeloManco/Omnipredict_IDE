import pandas as pd
import joblib
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UploadForm
from .models import PatientPrediction


CLASSIFIER = joblib.load("models/best_model.pkl")

@login_required
def upload_and_predict(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user

            # 2) read the uploaded file into pandas
            df = pd.read_csv(obj.data_file)        # or read_excel()
            features = df.values                  # adapt to your pipeline

            # 3) run the model
            proba = CLASSIFIER.predict_proba(features)[0, 1]
            label = "sarcopenic" if proba > 0.5 else "normal"

            # 4) save result
            obj.result = label
            obj.probability = float(proba)*100
            obj.save()

            return redirect("prediction-detail", pk=obj.pk)
    else:
        form = UploadForm()
    return render(request, "predictions/upload.html", {"form": form})

@login_required
def prediction_detail(request, pk):
    prediction = get_object_or_404(PatientPrediction, pk=pk, user=request.user)
    return render(request, "predictions/detail.html", {"p": prediction})

def home(request):
    return render(request, "home.html")

