import csv
import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import CollaborationEvent, SocialActivity, SubTask, Todo

User = get_user_model()


def _get_user_todos(request, include_archived=False):
    """Return todos filtered by the current user, shared collaborations, or guest tasks."""
    if request.user.is_authenticated:
        qs = Todo.objects.filter(
            Q(user=request.user) | Q(collaborators=request.user)
        ).distinct()
    else:
        qs = Todo.objects.filter(user__isnull=True)

    if not include_archived:
        qs = qs.filter(is_archived=False)
    return qs


def todo_list(request):
    active_view = request.GET.get("view", "list").strip()
    filter_preset = request.GET.get("filter", "").strip()
    status_filter = request.GET.get("status", "all").strip()
    is_archived_view = filter_preset == "archived" or status_filter == "archived"

    # Base queryset for current user
    all_user_todos = _get_user_todos(request, include_archived=is_archived_view)
    if is_archived_view:
        all_user_todos = all_user_todos.filter(is_archived=True)

    today = timezone.localdate()
    todos = all_user_todos

    # Smart Filter Presets
    if filter_preset == "today":
        todos = todos.filter(Q(due_date=today) | Q(is_pinned=True, done=False))
    elif filter_preset == "upcoming":
        seven_days_later = today + timedelta(days=7)
        todos = todos.filter(due_date__gte=today, due_date__lte=seven_days_later)
    elif filter_preset == "overdue":
        todos = todos.filter(due_date__lt=today, done=False)
    elif filter_preset == "pinned":
        todos = todos.filter(is_pinned=True)

    # Search query
    query = request.GET.get("q", "").strip()
    if query:
        todos = todos.filter(
            Q(title__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query)
        )

    # Status filter: all, active, completed
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
    sort_by = request.GET.get("sort", "default")
    sort_mapping = {
        "newest": ["-is_pinned", "-created_at"],
        "oldest": ["-is_pinned", "created_at"],
        "due_date": ["-is_pinned", "due_date", "-created_at"],
        "priority": ["-is_pinned", "priority", "-created_at"],
        "workload": ["-is_pinned", "-estimated_minutes"],
    }
    if sort_by in sort_mapping:
        todos = todos.order_by(*sort_mapping[sort_by])

    # Workload & Summary Metrics
    total_count = all_user_todos.count()
    completed_count = all_user_todos.filter(done=True).count()
    active_count = total_count - completed_count
    progress_percent = (
        int((completed_count / total_count) * 100) if total_count > 0 else 0
    )

    pinned_count = all_user_todos.filter(is_pinned=True, done=False).count()
    overdue_count = all_user_todos.filter(due_date__lt=today, done=False).count()
    today_count = all_user_todos.filter(due_date=today, done=False).count()

    total_est_minutes = sum(
        t.estimated_minutes for t in all_user_todos.filter(done=False)
    )
    workload_hours = total_est_minutes // 60
    workload_remainder_mins = total_est_minutes % 60
    if total_est_minutes:
        formatted_workload = (
            f"{workload_hours}h {workload_remainder_mins}m"
            if workload_remainder_mins
            else f"{workload_hours}h"
        )
    else:
        formatted_workload = "0m"

    # Distinct categories for auto-complete
    categories = sorted(
        {
            cat
            for cat in all_user_todos.values_list("category", flat=True)
            if cat and cat.strip()
        }
    )

    # Kanban Lanes
    kanban_todo = all_user_todos.filter(status="todo", done=False)
    kanban_in_progress = all_user_todos.filter(status="in_progress", done=False)
    kanban_done = all_user_todos.filter(Q(status="done") | Q(done=True))

    # Social & Collaborative Events
    social_activities = SocialActivity.objects.select_related("user")[:25]
    collaborative_events = CollaborationEvent.objects.prefetch_related(
        "participants"
    ).select_related("organizer")[:25]

    context = {
        "todos": todos,
        "active_view": active_view,
        "total_count": total_count,
        "completed_count": completed_count,
        "active_count": active_count,
        "progress_percent": progress_percent,
        "pinned_count": pinned_count,
        "overdue_count": overdue_count,
        "today_count": today_count,
        "formatted_workload": formatted_workload,
        "categories": categories,
        "current_query": query,
        "current_status": status_filter,
        "current_category": category_filter,
        "current_priority": priority_filter,
        "current_sort": sort_by,
        "current_filter": filter_preset,
        "is_archived_view": is_archived_view,
        "today_str": today.strftime("%Y-%m-%d"),
        "kanban_todo": kanban_todo,
        "kanban_in_progress": kanban_in_progress,
        "kanban_done": kanban_done,
        "social_activities": social_activities,
        "collaborative_events": collaborative_events,
    }
    return render(request, "todos/todo_list.html", context)


@require_POST
def todo_add(request):
    title = request.POST.get("title", "").strip()
    category = request.POST.get("category", "").strip()
    priority = request.POST.get("priority", "medium").strip()
    due_date_str = request.POST.get("due_date", "").strip()
    description = request.POST.get("description", "").strip()
    estimated_minutes_str = request.POST.get("estimated_minutes", "0").strip()
    is_pinned = request.POST.get("is_pinned") == "on"

    if priority not in ["low", "medium", "high"]:
        priority = "medium"

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            due_date = None

    try:
        estimated_minutes = max(0, int(estimated_minutes_str))
    except ValueError:
        estimated_minutes = 0

    if title:
        user = request.user if request.user.is_authenticated else None
        Todo.objects.create(
            user=user,
            title=title,
            category=category,
            priority=priority,
            due_date=due_date,
            description=description,
            estimated_minutes=estimated_minutes,
            is_pinned=is_pinned,
        )
        if request.user.is_authenticated:
            SocialActivity.objects.create(
                user=request.user,
                message=f'created a new task: "{title}" 🚀',
            )
        messages.success(request, f'Task "{title}" created successfully!')
    else:
        messages.error(request, "Task title cannot be empty.")

    return redirect("todo_list")


@require_POST
def todo_edit(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if (
        todo.user
        and todo.user != request.user
        and not todo.collaborators.filter(pk=request.user.pk).exists()
    ):
        raise Http404("Todo not found")

    title = request.POST.get("title", "").strip()
    if not title:
        messages.error(request, "Task title cannot be empty.")
        return redirect("todo_list")

    category = request.POST.get("category", "").strip()
    priority = request.POST.get("priority", "medium").strip()
    due_date_str = request.POST.get("due_date", "").strip()
    description = request.POST.get("description", "").strip()
    estimated_minutes_str = request.POST.get("estimated_minutes", "0").strip()
    is_pinned = request.POST.get("is_pinned") == "on"

    if priority in ["low", "medium", "high"]:
        todo.priority = priority

    if due_date_str:
        try:
            todo.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            todo.due_date = None
    else:
        todo.due_date = None

    try:
        todo.estimated_minutes = max(0, int(estimated_minutes_str))
    except ValueError:
        todo.estimated_minutes = 0

    todo.title = title
    todo.category = category
    todo.description = description
    todo.is_pinned = is_pinned
    todo.save()

    messages.success(request, f'Task "{todo.title}" updated!')
    return redirect("todo_list")


@require_POST
def todo_pin(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    todo.is_pinned = not todo.is_pinned
    todo.save()
    status_msg = "pinned to top" if todo.is_pinned else "unpinned"
    messages.success(request, f'Task "{todo.title}" {status_msg}.')
    return redirect("todo_list")


@require_POST
def todo_archive(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    todo.is_archived = not todo.is_archived
    todo.save()
    status_msg = "archived" if todo.is_archived else "restored from archive"
    messages.success(request, f'Task "{todo.title}" {status_msg}.')
    return redirect("todo_list")


@require_POST
def todo_toggle(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if (
        todo.user
        and todo.user != request.user
        and not todo.collaborators.filter(pk=request.user.pk).exists()
    ):
        raise Http404("Todo not found")

    todo.done = not todo.done
    if todo.done:
        todo.status = "done"
        if request.user.is_authenticated:
            SocialActivity.objects.create(
                user=request.user,
                message=f'completed the task: "{todo.title}"! ✅',
            )
    else:
        todo.status = "todo"
    todo.save()

    status_msg = "completed" if todo.done else "active"
    messages.success(request, f'Marked "{todo.title}" as {status_msg}.')
    return redirect("todo_list")


@require_POST
def todo_update_status(request, pk):
    """Update Kanban lane status (todo, in_progress, done)."""
    todo = get_object_or_404(Todo, pk=pk)
    if (
        todo.user
        and todo.user != request.user
        and not todo.collaborators.filter(pk=request.user.pk).exists()
    ):
        raise Http404("Todo not found")

    new_status = request.POST.get("status", "todo")
    if new_status in ["todo", "in_progress", "done"]:
        todo.status = new_status
        todo.done = new_status == "done"
        todo.save()
        messages.success(request, f'Moved "{todo.title}" to {new_status.title()}!')

    return redirect(request.META.get("HTTP_REFERER", "todo_list"))


@require_POST
def todo_share(request, pk):
    """Share a task with another user by username."""
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    target_username = request.POST.get("username", "").strip()
    if not target_username:
        messages.error(request, "Please specify a username to invite.")
        return redirect("todo_list")

    target_user = User.objects.filter(username=target_username).first()
    if not target_user:
        messages.error(request, f'User "{target_username}" was not found.')
        return redirect("todo_list")

    if target_user == request.user:
        messages.warning(request, "You already own this task.")
        return redirect("todo_list")

    todo.collaborators.add(target_user)
    SocialActivity.objects.create(
        user=request.user,
        message=f'invited @{target_user.username} to collaborate on "{todo.title}" 👥',
    )
    messages.success(request, f"Task shared with @{target_user.username} successfully!")
    return redirect("todo_list")


@require_POST
def subtask_add(request, pk):
    """Add a subtask to an existing task."""
    todo = get_object_or_404(Todo, pk=pk)
    if (
        todo.user
        and todo.user != request.user
        and not todo.collaborators.filter(pk=request.user.pk).exists()
    ):
        raise Http404("Todo not found")

    title = request.POST.get("title", "").strip()
    if title:
        SubTask.objects.create(todo=todo, title=title)
        messages.success(request, f'Added subtask "{title}".')
    return redirect("todo_list")


@require_POST
def subtask_toggle(request, pk):
    """Toggle completion status of a subtask."""
    subtask = get_object_or_404(SubTask, pk=pk)
    todo = subtask.todo
    if (
        todo.user
        and todo.user != request.user
        and not todo.collaborators.filter(pk=request.user.pk).exists()
    ):
        raise Http404("Subtask not found")

    subtask.done = not subtask.done
    subtask.save()
    return redirect("todo_list")


@require_POST
def subtask_delete(request, pk):
    """Delete a subtask."""
    subtask = get_object_or_404(SubTask, pk=pk)
    todo = subtask.todo
    if (
        todo.user
        and todo.user != request.user
        and not todo.collaborators.filter(pk=request.user.pk).exists()
    ):
        raise Http404("Subtask not found")

    subtask.delete()
    messages.success(request, "Subtask removed.")
    return redirect("todo_list")


@require_POST
def event_create(request):
    """Create a collaborative team event."""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to create collaboration events.")
        return redirect("login")

    title = request.POST.get("title", "").strip()
    date_str = request.POST.get("event_date", "").strip()
    description = request.POST.get("description", "").strip()

    if not title or not date_str:
        messages.error(request, "Event title and date are required.")
        return redirect("/?view=events")

    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid event date format.")
        return redirect("/?view=events")

    event = CollaborationEvent.objects.create(
        organizer=request.user,
        title=title,
        description=description,
        event_date=event_date,
    )
    event.participants.add(request.user)

    SocialActivity.objects.create(
        user=request.user,
        message=f'scheduled a collaborative event: "{title}" on {event_date} 📅',
    )
    messages.success(request, f'Event "{title}" scheduled!')
    return redirect("/?view=events")


@require_POST
def event_join(request, pk):
    """Join or leave a collaborative event."""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to join events.")
        return redirect("login")

    event = get_object_or_404(CollaborationEvent, pk=pk)
    if event.participants.filter(pk=request.user.pk).exists():
        event.participants.remove(request.user)
        messages.success(request, f'Left event "{event.title}".')
    else:
        event.participants.add(request.user)
        SocialActivity.objects.create(
            user=request.user,
            message=f'joined the collaborative event "{event.title}"! 🤝',
        )
        messages.success(request, f'Joined event "{event.title}"!')
    return redirect("/?view=events")


@require_POST
def social_post(request):
    """Post an update to the Social Hub feed."""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to post in the social area.")
        return redirect("login")

    message = request.POST.get("message", "").strip()
    if message:
        SocialActivity.objects.create(user=request.user, message=message)
        messages.success(request, "Update posted to Social Hub!")
    return redirect("/?view=social")


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

    new_todo = Todo.objects.create(
        user=todo.user,
        title=f"{todo.title} (Copy)",
        category=todo.category,
        priority=todo.priority,
        due_date=todo.due_date,
        description=todo.description,
        estimated_minutes=todo.estimated_minutes,
        is_pinned=todo.is_pinned,
        done=False,
    )
    # Duplicate subtasks as well
    for st in todo.subtasks.all():
        SubTask.objects.create(todo=new_todo, title=st.title, done=False)

    messages.success(request, f'Duplicated "{todo.title}".')
    return redirect("todo_list")


@require_POST
def todo_clear_completed(request):
    todos = _get_user_todos(request, include_archived=True).filter(done=True)
    count = todos.count()
    todos.delete()
    messages.success(request, f"Cleared {count} completed task(s).")
    return redirect("todo_list")


@require_POST
def todo_mark_all(request):
    todos = _get_user_todos(request).filter(done=False)
    count = todos.count()
    todos.update(done=True, status="done")
    messages.success(request, f"Marked {count} task(s) as completed.")
    return redirect("todo_list")


def todo_export_json(request):
    todos = _get_user_todos(request, include_archived=True)
    data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "due_date": str(t.due_date) if t.due_date else None,
            "estimated_minutes": t.estimated_minutes,
            "is_pinned": t.is_pinned,
            "is_archived": t.is_archived,
            "done": t.done,
            "subtasks": [
                {"title": st.title, "done": st.done} for st in t.subtasks.all()
            ],
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
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
    todos = _get_user_todos(request, include_archived=True)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="todos_export.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Title",
            "Category",
            "Priority",
            "Status",
            "Due Date",
            "Est Minutes",
            "Pinned",
            "Archived",
            "Done",
            "Created At",
        ]
    )
    for t in todos:
        writer.writerow(
            [
                t.id,
                t.title,
                t.category,
                t.priority,
                t.status,
                t.due_date or "",
                t.estimated_minutes,
                "Yes" if t.is_pinned else "No",
                "Yes" if t.is_archived else "No",
                "Yes" if t.done else "No",
                t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )
    return response


def todo_export_ical(request):
    """Export tasks with due dates as an iCalendar (.ics) calendar file."""
    todos = _get_user_todos(request, include_archived=False).filter(
        due_date__isnull=False
    )
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Anyone Can Build//Todo Calendar//EN",
        "CALSCALE:GREGORIAN",
    ]
    now_stamp = timezone.now().strftime("%Y%m%dT%H%M%SZ")

    for t in todos:
        date_str = t.due_date.strftime("%Y%m%d")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:todo-{t.id}@anyone-can-build",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART;VALUE=DATE:{date_str}",
                f"SUMMARY:{t.title}",
                f"DESCRIPTION:{t.description or t.category or ''}",
                f"STATUS:{'COMPLETED' if t.done else 'NEEDS-ACTION'}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    response = HttpResponse("\r\n".join(lines), content_type="text/calendar")
    response["Content-Disposition"] = 'attachment; filename="todos_calendar.ics"'
    return response


@require_POST
def todo_import_json(request):
    """Import tasks from an uploaded JSON file."""
    upload_file = request.FILES.get("json_file")
    if not upload_file:
        messages.error(request, "Please choose a JSON file to import.")
        return redirect("todo_list")

    try:
        data = json.load(upload_file)
        if not isinstance(data, list):
            raise ValueError("Root element must be a list")

        imported_count = 0
        user = request.user if request.user.is_authenticated else None

        for item in data:
            title = str(item.get("title", "")).strip()
            if not title:
                continue

            due_date = None
            due_str = item.get("due_date")
            if due_str:
                try:
                    due_date = datetime.strptime(str(due_str), "%Y-%m-%d").date()
                except ValueError:
                    due_date = None

            priority = item.get("priority", "medium")
            if priority not in ["low", "medium", "high"]:
                priority = "medium"

            try:
                est = max(0, int(item.get("estimated_minutes", 0)))
            except (ValueError, TypeError):
                est = 0

            new_todo = Todo.objects.create(
                user=user,
                title=title,
                description=str(item.get("description", "")),
                category=str(item.get("category", "")),
                priority=priority,
                due_date=due_date,
                estimated_minutes=est,
                is_pinned=bool(item.get("is_pinned", False)),
                done=bool(item.get("done", False)),
                status=item.get("status", "done" if item.get("done") else "todo"),
            )
            subtasks_data = item.get("subtasks", [])
            if isinstance(subtasks_data, list):
                for st in subtasks_data:
                    st_title = str(st.get("title", "")).strip()
                    if st_title:
                        SubTask.objects.create(
                            todo=new_todo,
                            title=st_title,
                            done=bool(st.get("done", False)),
                        )
            imported_count += 1

        messages.success(request, f"Successfully imported {imported_count} task(s)!")
    except Exception as e:
        messages.error(request, f"Failed to import JSON: {e}")

    return redirect("todo_list")


def api_todos(request):
    todos = _get_user_todos(request, include_archived=False)
    data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "due_date": str(t.due_date) if t.due_date else None,
            "estimated_minutes": t.estimated_minutes,
            "is_pinned": t.is_pinned,
            "done": t.done,
            "subtasks_count": t.total_subtasks_count,
            "completed_subtasks": t.completed_subtasks_count,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
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
            SocialActivity.objects.create(
                user=user,
                message="just joined the platform! 👋",
            )
            messages.success(
                request, f"Welcome to your To-Do workspace, {user.username}!"
            )
            return redirect("todo_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
