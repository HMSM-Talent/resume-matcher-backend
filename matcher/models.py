from django.db import models
from resumes.models import Resume, JobDescription
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class SimilarityScore(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='similarity_scores'
    )
    job_description = models.ForeignKey(
        JobDescription,
        on_delete=models.CASCADE,
        related_name='similarity_scores'
    )
    score = models.FloatField(
        validators=[
            MinValueValidator(0.0, message="Score must be >= 0.0"),
            MaxValueValidator(1.0, message="Score must be <= 1.0")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('resume', 'job_description')
        ordering = ['-score']
        indexes = [
            models.Index(fields=['resume', 'job_description']),
            models.Index(fields=['score']),
        ]

    def clean(self):
        if self.score < 0 or self.score > 1:
            raise ValidationError("Score must be between 0.0 and 1.0")

    def __str__(self):
        return f"Score: {self.score:.2f} | Resume ID: {self.resume_id} | JD ID: {self.job_description_id}"