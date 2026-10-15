from django.urls import path

from . import views

urlpatterns = [
    path("", views.welcome_page, name="welcome"),
    path("app/", views.todo_list, name="todo_list"),
    path("add/", views.todo_add, name="todo_add"),
    path("<int:pk>/edit/", views.todo_edit, name="todo_edit"),
    path("<int:pk>/toggle/", views.todo_toggle, name="todo_toggle"),
    path("<int:pk>/status/", views.todo_update_status, name="todo_update_status"),
    path("<int:pk>/pin/", views.todo_pin, name="todo_pin"),
    path("<int:pk>/archive/", views.todo_archive, name="todo_archive"),
    path("<int:pk>/share/", views.todo_share, name="todo_share"),
    path("<int:pk>/delete/", views.todo_delete, name="todo_delete"),
    path("<int:pk>/duplicate/", views.todo_duplicate, name="todo_duplicate"),
    path("<int:pk>/subtask/add/", views.subtask_add, name="subtask_add"),
    path("subtask/<int:pk>/toggle/", views.subtask_toggle, name="subtask_toggle"),
    path("subtask/<int:pk>/delete/", views.subtask_delete, name="subtask_delete"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:pk>/join/", views.event_join, name="event_join"),
    path("social/post/", views.social_post, name="social_post"),
    path("set-language/<str:lang_code>/", views.set_language_view, name="set_language"),
    path("<int:pk>/time-log/", views.todo_time_log, name="todo_time_log"),
    path(
        "<int:pk>/smart-breakdown/",
        views.todo_smart_breakdown,
        name="todo_smart_breakdown",
    ),
    path("projects/add/", views.project_add, name="project_add"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    path("habits/add/", views.habit_add, name="habit_add"),
    path("habits/<int:pk>/check/", views.habit_toggle, name="habit_toggle"),
    path("habits/<int:pk>/delete/", views.habit_delete, name="habit_delete"),
    path("<int:pk>/favorite/", views.todo_favorite, name="todo_favorite"),
    path("<int:pk>/trash/", views.todo_trash, name="todo_trash"),
    path("<int:pk>/restore/", views.todo_restore, name="todo_restore"),
    path("trash/empty/", views.todo_empty_trash, name="todo_empty_trash"),
    path("<int:pk>/comment/", views.task_comment_add, name="task_comment_add"),
    path("notifications/clear/", views.notification_clear, name="notification_clear"),
    path("clear-completed/", views.todo_clear_completed, name="todo_clear_completed"),
    path("mark-all/", views.todo_mark_all, name="todo_mark_all"),
    path("export/json/", views.todo_export_json, name="todo_export_json"),
    path("export/csv/", views.todo_export_csv, name="todo_export_csv"),
    path("export/ical/", views.todo_export_ical, name="todo_export_ical"),
    path("import/json/", views.todo_import_json, name="todo_import_json"),
    path("api/todos/", views.api_todos, name="api_todos"),
    path("api/ai-solve/", views.api_ai_solve, name="api_ai_solve"),
    # Second Brain / Wiki
    path("wiki/add/", views.wiki_add, name="wiki_add"),
    path("wiki/<int:pk>/edit/", views.wiki_edit, name="wiki_edit"),
    path("wiki/<int:pk>/delete/", views.wiki_delete, name="wiki_delete"),
    # Finance Tracker
    path("finance/transaction/add/", views.transaction_add, name="transaction_add"),
    path(
        "finance/transaction/<int:pk>/delete/",
        views.transaction_delete,
        name="transaction_delete",
    ),
    path("finance/savings/add/", views.savings_add, name="savings_add"),
    path(
        "finance/savings/<int:pk>/contribute/",
        views.savings_contribute,
        name="savings_contribute",
    ),
    path(
        "finance/savings/<int:pk>/delete/",
        views.savings_delete,
        name="savings_delete",
    ),
    # Journal & Mood
    path("journal/entry/add/", views.journal_add, name="journal_add"),
    path(
        "journal/entry/<int:pk>/delete/",
        views.journal_delete,
        name="journal_delete",
    ),
    # Media & Bookshelf
    path("media/item/add/", views.media_add, name="media_add"),
    path(
        "media/item/<int:pk>/status/",
        views.media_status_update,
        name="media_status_update",
    ),
    path("media/item/<int:pk>/delete/", views.media_delete, name="media_delete"),
    # RPG Gamification
    path("rpg/reward/add/", views.rpg_reward_add, name="rpg_reward_add"),
    path(
        "rpg/reward/<int:pk>/redeem/",
        views.rpg_reward_redeem,
        name="rpg_reward_redeem",
    ),
    path(
        "rpg/reward/<int:pk>/delete/",
        views.rpg_reward_delete,
        name="rpg_reward_delete",
    ),
]
