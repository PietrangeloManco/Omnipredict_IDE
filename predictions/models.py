from django.contrib.auth import get_user_model
from django.db import models

class PatientPrediction(models.Model):
    user        = models.ForeignKey(get_user_model(),
                                    on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    data_file   = models.FileField(upload_to="uploads/")
    result      = models.CharField(max_length=50, blank=True)
    probability = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} – {self.result} ({self.uploaded_at:%Y-%m-%d})"
