import csv
import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Todo


def _get_user_todos(request):
    """Return todos filtered by the current user or guest tasks."""
    if request.user.is_authenticated:
        return Todo.objects.filter(user=request.user)
    return Todo.objects.filter(user__isnull=True)


def todo_list(request):
    all_user_todos = _get_user_todos(request)

    # Search query
    query = request.GET.get("q", "").strip()
    todos = all_user_todos
    if query:
        todos = todos.filter(
            Q(title__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query)
        )

    # Status filter: all, active, completed
    status_filter = request.GET.get("status", "all")
    if status_filter == "active":
        todos = todos.filter(done=False)
    elif status_filter == "completed":
        todos = todos.filter(done=True)

    # Category filter
    category_filter = request.GET.get("category", "").strip()
    if category_filter:
        todos = todos.filter(category=category_filter)

    # Priority filter
    priority_filter = request.GET.get("priority", "").strip()
    if priority_filter in ["low", "medium", "high"]:
        todos = todos.filter(priority=priority_filter)

    # Sorting
    sort_by = request.GET.get("sort", "-created_at")
    valid_sorts = {
        "-created_at": "-created_at",
        "created_at": "created_at",
        "due_date": "due_date",
        "priority": "priority",
    }
    todos = todos.order_by(valid_sorts.get(sort_by, "-created_at"))

    # Metrics
    total_count = all_user_todos.count()
    completed_count = all_user_todos.filter(done=True).count()
    active_count = total_count - completed_count
    progress_percent = (
        int((completed_count / total_count) * 100) if total_count > 0 else 0
    )

    # Distinct categories for filter buttons
    categories = sorted(
        {
            cat
            for cat in all_user_todos.values_list("category", flat=True)
            if cat and cat.strip()
        }
    )

    context = {
        "todos": todos,
        "total_count": total_count,
        "completed_count": completed_count,
        "active_count": active_count,
        "progress_percent": progress_percent,
        "categories": categories,
        "current_query": query,
        "current_status": status_filter,
        "current_category": category_filter,
        "current_priority": priority_filter,
        "current_sort": sort_by,
    }
    return render(request, "todos/todo_list.html", context)


@require_POST
def todo_add(request):
    title = request.POST.get("title", "").strip()
    category = request.POST.get("category", "").strip()
    priority = request.POST.get("priority", "medium").strip()
    due_date_str = request.POST.get("due_date", "").strip()
    description = request.POST.get("description", "").strip()

    if priority not in ["low", "medium", "high"]:
        priority = "medium"

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            due_date = None

    if title:
        user = request.user if request.user.is_authenticated else None
        Todo.objects.create(
            user=user,
            title=title,
            category=category,
            priority=priority,
            due_date=due_date,
            description=description,
        )
        messages.success(request, f'Task "{title}" added!')
    else:
        messages.error(request, "Task title cannot be empty.")

    return redirect("todo_list")


@require_POST
def todo_toggle(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    todo.done = not todo.done
    todo.save()
    status_msg = "completed" if todo.done else "active"
    messages.success(request, f'Marked "{todo.title}" as {status_msg}.')
    return redirect("todo_list")


@require_POST
def todo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    title = todo.title
    todo.delete()
    messages.success(request, f'Task "{title}" deleted.')
    return redirect("todo_list")


@require_POST
def todo_duplicate(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    Todo.objects.create(
        user=todo.user,
        title=f"{todo.title} (Copy)",
        category=todo.category,
        priority=todo.priority,
        due_date=todo.due_date,
        description=todo.description,
        done=False,
    )
    messages.success(request, f'Duplicated "{todo.title}".')
    return redirect("todo_list")


@require_POST
def todo_clear_completed(request):
    todos = _get_user_todos(request).filter(done=True)
    count = todos.count()
    todos.delete()
    messages.success(request, f"Cleared {count} completed task(s).")
    return redirect("todo_list")


@require_POST
def todo_mark_all(request):
    todos = _get_user_todos(request).filter(done=False)
    count = todos.count()
    todos.update(done=True)
    messages.success(request, f"Marked {count} task(s) as completed.")
    return redirect("todo_list")


def todo_export_json(request):
    todos = _get_user_todos(request)
    data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "due_date": str(t.due_date) if t.due_date else None,
            "done": t.done,
            "created_at": t.created_at.isoformat(),
        }
        for t in todos
    ]
    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type="application/json",
    )
    response["Content-Disposition"] = 'attachment; filename="todos_export.json"'
    return response


def todo_export_csv(request):
    todos = _get_user_todos(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="todos_export.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ["ID", "Title", "Category", "Priority", "Due Date", "Done", "Created At"]
    )
    for t in todos:
        writer.writerow(
            [
                t.id,
                t.title,
                t.category,
                t.priority,
                t.due_date or "",
                "Yes" if t.done else "No",
                t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )
    return response


def api_todos(request):
    todos = _get_user_todos(request)
    data = [
        {
            "id": t.id,
            "title": t.title,
            "category": t.category,
            "priority": t.priority,
            "due_date": str(t.due_date) if t.due_date else None,
            "done": t.done,
            "created_at": t.created_at.isoformat(),
        }
        for t in todos
    ]
    return JsonResponse({"todos": data})


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to your To-Do list, {user.username}!")
            return redirect("todo_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
