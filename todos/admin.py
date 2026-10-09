from django.contrib import admin

from .models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "category",
        "priority",
        "due_date",
        "done",
        "created_at",
    )
    list_filter = ("done", "priority", "category", "created_at")
    search_fields = ("title", "description", "category")
    list_editable = ("done", "priority")
