from django.conf import settings
from django.db import models
from django.utils import timezone


class Todo(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="todos",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=50, blank=True, default="")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
    )
    due_date = models.DateField(null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(default=0, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date and not self.done:
            return self.due_date < timezone.localdate()
        return False

    @property
    def is_due_today(self):
        if self.due_date and not self.done:
            return self.due_date == timezone.localdate()
        return False

    @property
    def formatted_duration(self):
        """Format estimated minutes into human-readable duration."""
        if not self.estimated_minutes:
            return ""
        if self.estimated_minutes < 60:
            return f"{self.estimated_minutes}m"
        hours = self.estimated_minutes // 60
        mins = self.estimated_minutes % 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"
