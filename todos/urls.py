from django.urls import path

from . import views

urlpatterns = [
    path("", views.todo_list, name="todo_list"),
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
    path("clear-completed/", views.todo_clear_completed, name="todo_clear_completed"),
    path("mark-all/", views.todo_mark_all, name="todo_mark_all"),
    path("export/json/", views.todo_export_json, name="todo_export_json"),
    path("export/csv/", views.todo_export_csv, name="todo_export_csv"),
    path("export/ical/", views.todo_export_ical, name="todo_export_ical"),
    path("import/json/", views.todo_import_json, name="todo_import_json"),
    path("api/todos/", views.api_todos, name="api_todos"),
]
