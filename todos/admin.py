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
        "estimated_minutes",
        "is_pinned",
        "is_archived",
        "done",
        "created_at",
    )
    list_filter = (
        "done",
        "is_pinned",
        "is_archived",
        "priority",
        "category",
        "created_at",
    )
    search_fields = ("title", "description", "category")
    list_editable = ("done", "priority", "is_pinned", "is_archived")
    actions = ["mark_done", "pin_todos", "archive_todos"]

    @admin.action(description="Mark selected tasks as done")
    def mark_done(self, request, queryset):
        queryset.update(done=True)

    @admin.action(description="Pin selected tasks to top")
    def pin_todos(self, request, queryset):
        queryset.update(is_pinned=True)

    @admin.action(description="Archive selected tasks")
    def archive_todos(self, request, queryset):
        queryset.update(is_archived=True)
