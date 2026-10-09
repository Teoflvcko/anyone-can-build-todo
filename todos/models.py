from django.db import models


class Todo(models.Model):
    title = models.CharField(max_length=200)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title
