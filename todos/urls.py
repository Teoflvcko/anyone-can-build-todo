from django.urls import path

from . import views

urlpatterns = [
    path("", views.todo_list, name="todo_list"),
    path("add/", views.todo_add, name="todo_add"),
    path("<int:pk>/toggle/", views.todo_toggle, name="todo_toggle"),
    path("<int:pk>/delete/", views.todo_delete, name="todo_delete"),
    path("<int:pk>/duplicate/", views.todo_duplicate, name="todo_duplicate"),
    path("clear-completed/", views.todo_clear_completed, name="todo_clear_completed"),
    path("mark-all/", views.todo_mark_all, name="todo_mark_all"),
    path("export/json/", views.todo_export_json, name="todo_export_json"),
    path("export/csv/", views.todo_export_csv, name="todo_export_csv"),
    path("api/todos/", views.api_todos, name="api_todos"),
]
