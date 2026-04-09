import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from .forms import ManualPredictForm, UploadForm
from .models import PatientPrediction

logger = logging.getLogger(__name__)

# ---- Load artifacts ----
MODEL_DIR = Path(getattr(settings, "MODEL_DIR", Path(settings.BASE_DIR) / "models"))
FEATURE_COLUMNS_JSON = Path(
    getattr(settings, "FEATURE_COLUMNS_JSON", MODEL_DIR / "feature_columns.json")
)
PIPE = None
CLASSIFIER_ONLY = None
RAW_FEATURE_COLUMNS = None


def _patch_legacy_sklearn_artifacts(obj, seen=None):
    """Populate attrs expected by newer scikit-learn releases for old pickles."""
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return
    seen.add(obj_id)

    if isinstance(obj, Pipeline) and not hasattr(obj, "transform_input"):
        obj.transform_input = None

    if (
        isinstance(obj, SimpleImputer)
        and not hasattr(obj, "_fill_dtype")
        and hasattr(obj, "_fit_dtype")
    ):
        obj._fill_dtype = obj._fit_dtype

    named_steps = getattr(obj, "named_steps", None)
    if named_steps:
        for child in named_steps.values():
            _patch_legacy_sklearn_artifacts(child, seen)

    transformers = getattr(obj, "transformers_", None)
    if transformers:
        for _, child, _ in transformers:
            _patch_legacy_sklearn_artifacts(child, seen)


def _get_raw_feature_columns(pipe):
    json_path = FEATURE_COLUMNS_JSON
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            return list(json.load(f))

    # Extract from ColumnTransformer inside pipeline
    pre = pipe.named_steps.get("pre") or pipe.named_steps.get("preprocessor")
    cols = []
    if hasattr(pre, "transformers_"):
        for name, _, col_names in pre.transformers_:
            if name == "remainder":
                continue
            if isinstance(col_names, (list, tuple, np.ndarray, pd.Index)):
                cols.extend([str(c) for c in col_names])
    return cols


def _ensure_artifacts_loaded():
    global PIPE, CLASSIFIER_ONLY, RAW_FEATURE_COLUMNS

    if PIPE is not None and RAW_FEATURE_COLUMNS is not None:
        return

    pipeline_path = MODEL_DIR / "best_pipeline.pkl"
    if not pipeline_path.exists():
        raise FileNotFoundError(
            "The Omnipredict model artifacts are not included in this public repository. "
            "Provide the proprietary files in the configured model directory to enable inference."
        )

    pipe = joblib.load(pipeline_path)
    _patch_legacy_sklearn_artifacts(pipe)

    # Optional: keep classifier-only to support "already preprocessed" files exactly like before.
    try:
        classifier_only = joblib.load(MODEL_DIR / "best_model.pkl")
        _patch_legacy_sklearn_artifacts(classifier_only)
    except Exception:
        classifier_only = None  # if you don't have it, users should upload RAW

    PIPE = pipe
    CLASSIFIER_ONLY = classifier_only
    RAW_FEATURE_COLUMNS = _get_raw_feature_columns(pipe)


def _align_raw_row(row_dict: dict) -> pd.DataFrame:
    _ensure_artifacts_loaded()
    row = {col: np.nan for col in RAW_FEATURE_COLUMNS}

    # ----- Fix gender -----
    g = row_dict.get("gender")
    if g:
        g = g.lower()
        if g in ["m", "male"]:
            row["gender"] = "male"
        elif g in ["f", "female"]:
            row["gender"] = "female"

    # ----- Fix SNP normalisation -----
    for snp in ["rs174537", "rs174626", "rs174579", "rs174593",
                "rs526126", "rs953413"]:
        if snp in row_dict and row_dict[snp]:
            row[snp] = row_dict[snp].upper()

    # ----- Map simple numeric fields -----
    for field in ["bmi", "Hand_Grip", "Omega3_Index", "SCAT"]:
        if field in row_dict and row_dict[field] not in ("", None):
            row[field] = float(row_dict[field])

    # ----- The rest stays NaN and is imputed by pipeline -----
    return pd.DataFrame([row])


def _predict_with_pipeline_from_raw(row_dict: dict):
    _ensure_artifacts_loaded()
    df = _align_raw_row(row_dict)
    proba = float(PIPE.predict_proba(df)[0, 1])
    label = "Positivo" if proba > 0.5 else "Negativo"
    return label, proba * 100.0


def _predict_from_uploaded_file(file_obj, already_preprocessed: bool):
    _ensure_artifacts_loaded()
    name = file_obj.name.lower()
    logger.info(f"Uploaded file: {name}, already_preprocessed={already_preprocessed}")

    if name.endswith(".csv"):
        df = pd.read_csv(file_obj)
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_obj)
    else:
        raise ValueError("Please upload a CSV, XLSX, or XLS file.")

    if df.shape[0] == 0:
        raise ValueError("Your file is empty.")

    logger.info(f"Uploaded file shape: {df.shape}")

    if already_preprocessed and CLASSIFIER_ONLY is not None:
        X = df.values
        proba = float(CLASSIFIER_ONLY.predict_proba(X)[0, 1])
        label = "Positive" if proba > 0.5 else "Negative"
        return label, proba * 100.0

    # RAW data -> pipeline
    row0 = df.iloc[0].to_dict()
    return _predict_with_pipeline_from_raw(row0)


@login_required
def upload_and_predict(request):
    if request.method == "POST":
        # If a file field present or the checkbox posted, use the file path
        if request.FILES.get("data_file") or ("already_preprocessed" in request.POST):
            upload_form = UploadForm(request.POST, request.FILES)
            manual_form = ManualPredictForm()
            if upload_form.is_valid():
                try:
                    label, probability = _predict_from_uploaded_file(
                        upload_form.cleaned_data["data_file"],
                        upload_form.cleaned_data.get("already_preprocessed", False),
                    )
                except Exception as e:
                    messages.error(request, str(e))
                    return render(request, "predictions/upload.html", {
                        "form": upload_form,
                        "manual_form": manual_form
                    })

                obj = PatientPrediction.objects.create(
                    user=request.user,
                    result=label,
                    probability=probability
                )
                return redirect("prediction-detail", pk=obj.pk)

        # Manual form path
        manual_form = ManualPredictForm(request.POST)
        upload_form = UploadForm()
        if manual_form.is_valid():
            cd = manual_form.cleaned_data
            row_dict = {
                "gender": cd.get("gender"),
                "bmi": cd.get("bmi"),
                "Omega3_Index": cd.get("Omega3_Index"),
                "Hand_Grip": cd.get("Hand_Grip"),
                "rs174537": cd.get("rs174537"),
                "rs174626": cd.get("rs174626"),
                "SCAT": cd.get("SCAT"),
            }
            label, probability = _predict_with_pipeline_from_raw(row_dict)

            obj = PatientPrediction.objects.create(
                user=request.user,
                result=label,
                probability=probability
            )
            return redirect("prediction-detail", pk=obj.pk)
    else:
        upload_form = UploadForm()
        manual_form = ManualPredictForm()

    return render(request, "predictions/upload.html", {
        "form": upload_form,
        "manual_form": manual_form
    })


@login_required
def prediction_detail(request, pk):
    prediction = get_object_or_404(PatientPrediction, pk=pk, user=request.user)
    return render(request, "predictions/detail.html", {"p": prediction})


def home(request):
    return render(request, "home.html")
