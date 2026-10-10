from django.contrib import admin

from .models import CollaborationEvent, SocialActivity, SubTask, Todo


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "status",
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
        "status",
        "done",
        "is_pinned",
        "is_archived",
        "priority",
        "category",
        "created_at",
    )
    search_fields = ("title", "description", "category")
    list_editable = ("status", "done", "priority", "is_pinned", "is_archived")
    filter_horizontal = ("collaborators",)
    inlines = [SubTaskInline]
    actions = ["mark_done", "pin_todos", "archive_todos"]

    @admin.action(description="Mark selected tasks as done")
    def mark_done(self, request, queryset):
        queryset.update(done=True, status="done")

    @admin.action(description="Pin selected tasks to top")
    def pin_todos(self, request, queryset):
        queryset.update(is_pinned=True)

    @admin.action(description="Archive selected tasks")
    def archive_todos(self, request, queryset):
        queryset.update(is_archived=True)


@admin.register(CollaborationEvent)
class CollaborationEventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "event_date", "created_at")
    list_filter = ("event_date", "created_at")
    search_fields = ("title", "description", "organizer__username")
    filter_horizontal = ("participants",)


@admin.register(SocialActivity)
class SocialActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "message")
