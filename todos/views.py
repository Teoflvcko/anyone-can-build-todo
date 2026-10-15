import calendar
import csv
import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .models import (
    CollaborationEvent,
    Habit,
    HabitLog,
    JournalEntry,
    MediaItem,
    Notification,
    Project,
    RpgReward,
    SavingsGoal,
    SocialActivity,
    SubTask,
    TaskComment,
    Todo,
    Transaction,
    UserProfileRPG,
    WikiPage,
)

User = get_user_model()

TRANSLATIONS = {
    "en": {
        "brand": "TaskFlow Quantum",
        "welcome_intro": "Welcome Page",
        "start_app": "Start Application",
        "my_tasks": "My Tasks",
        "kanban": "Kanban Board",
        "calendar": "Calendar",
        "eisenhower": "Eisenhower Matrix",
        "analytics": "Analytics & Velocity",
        "leaderboard": "Leaderboard",
        "focus_timer": "Focus Timer",
        "trash": "Trash Bin",
        "social": "Social Hub",
        "collab_events": "Collab Events",
        "notifications": "Notifications",
        "mark_all_read": "Mark All as Read",
        "no_notifications": "No notifications yet",
        "tags": "Tags",
        "comments": "Comments",
        "add_comment": "Write a comment...",
        "shortcuts": "Shortcuts",
        "quick_template": "Template",
        "today_btn": "Today",
        "prev": "Prev",
        "next": "Next",
        "total": "Total",
        "pending": "Pending",
        "completed": "Completed",
        "pinned": "Pinned",
        "overdue": "Overdue",
        "workload": "Workload",
        "xp_level": "Level",
        "add_task": "Add Task",
        "what_needs_doing": "What needs doing?",
        "category": "Category",
        "priority": "Priority",
        "due_date": "Due date",
        "est_min": "Est. min",
        "pin_to_top": "Pin to Top",
        "share": "Share",
        "delete": "Delete",
        "edit": "Edit",
        "archive": "Archive",
        "restore": "Restore",
        "empty_trash": "Empty Trash",
        "urgent_important": "🔥 Urgent & Important (Do First)",
        "not_urgent_important": "📅 Important, Not Urgent (Schedule)",
        "urgent_not_important": "⚡ Urgent, Not Important (Delegate)",
        "not_urgent_not_important": "🌱 Neither (Eliminate)",
        "timeline": "Timeline Gantt",
        "habits": "Habits & Streaks",
        "zen_focus": "Zen Focus Mode",
        "theme_studio": "Theme & Sound Studio",
        "projects": "Projects",
        "smart_helper": "AI Task Helper",
        "standup_summary": "Daily Standup Summary",
        "actual_time": "Actual Time",
        "wiki": "Second Brain & Wiki",
        "finance": "Finance & Budget",
        "journal": "Daily Journal & Mood",
        "media": "Bookshelf & Media",
        "rpg": "Productivity RPG",
        "soundscapes": "Focus Soundscapes",
        "ai_solver": "AI Problem Solver",
    },
    "it": {
        "brand": "TaskFlow Quantum",
        "welcome_intro": "Pagina Iniziale",
        "start_app": "Entra nell'Applicazione",
        "my_tasks": "I Miei Compiti",
        "kanban": "Tabellone Kanban",
        "calendar": "Calendario",
        "eisenhower": "Matrice Eisenhower",
        "analytics": "Analisi & Produttività",
        "leaderboard": "Classifica Team",
        "focus_timer": "Timer Concentrazione",
        "trash": "Cestino",
        "social": "Area Social",
        "collab_events": "Eventi Condivisi",
        "notifications": "Notifiche",
        "mark_all_read": "Segna tutti come letti",
        "no_notifications": "Nessuna notifica al momento",
        "tags": "Tag",
        "comments": "Commenti",
        "add_comment": "Scrivi un commento...",
        "shortcuts": "Scorciatoie",
        "quick_template": "Modello",
        "today_btn": "Oggi",
        "prev": "Prec",
        "next": "Succ",
        "total": "Totale",
        "pending": "In Sospeso",
        "completed": "Completati",
        "pinned": "In Evidenza",
        "overdue": "Scaduti",
        "workload": "Carico di Lavoro",
        "xp_level": "Livello",
        "add_task": "Aggiungi Compito",
        "what_needs_doing": "Cosa c'è da fare?",
        "category": "Categoria",
        "priority": "Priorità",
        "due_date": "Scadenza",
        "est_min": "Min. stimati",
        "pin_to_top": "Fissa in Alto",
        "share": "Condividi",
        "delete": "Elimina",
        "edit": "Modifica",
        "archive": "Archivia",
        "restore": "Ripristina",
        "empty_trash": "Svuota Cestino",
        "urgent_important": "🔥 Urgente e Importante (Fai Subito)",
        "not_urgent_important": "📅 Importante, Non Urgente (Pianifica)",
        "urgent_not_important": "⚡ Urgente, Non Importante (Delega)",
        "not_urgent_not_important": "🌱 Né Urgente né Importante (Elimina)",
        "timeline": "Timeline Gantt",
        "habits": "Abitudini & Costanza",
        "zen_focus": "Modalità Zen",
        "theme_studio": "Studio Temi & Suoni",
        "projects": "Progetti",
        "smart_helper": "Assistente AI",
        "standup_summary": "Riepilogo Standup Giornaliero",
        "actual_time": "Tempo Effettivo",
        "wiki": "Second Brain & Wiki",
        "finance": "Finanze & Budget",
        "journal": "Diario & Umore",
        "media": "Libreria & Media",
        "rpg": "Gioco di Ruolo RPG",
        "soundscapes": "Oasi Sonora & Respiro",
        "ai_solver": "Risolutore Problemi AI",
    },
}


def _award_rpg_xp(request, xp=15, coins=5, stat="discipline"):
    """Award RPG XP, Coins and stat increments to user or session guest."""
    user = request.user if request.user.is_authenticated else None
    profile, _ = UserProfileRPG.objects.get_or_create(user=user)
    profile.xp += xp
    profile.coins += coins
    if stat == "discipline":
        profile.discipline_stat += 1
    elif stat == "focus":
        profile.focus_stat += 1
    elif stat == "creativity":
        profile.creativity_stat += 1
    elif stat == "vitality":
        profile.vitality_stat += 1
    profile.save()


def _get_user_todos(request, include_archived=False, include_deleted=False):
    """Return todos filtered by the current user or guest tasks."""
    if request.user.is_authenticated:
        qs = Todo.objects.filter(
            Q(user=request.user) | Q(collaborators=request.user)
        ).distinct()
    else:
        qs = Todo.objects.filter(user__isnull=True)

    if include_deleted:
        return qs.filter(is_deleted=True)
    qs = qs.filter(is_deleted=False)

    if not include_archived:
        qs = qs.filter(is_archived=False)
    return qs


def set_language_view(request, lang_code):
    """Switch language between English ('en') and Italian ('it')."""
    if lang_code in ["en", "it"]:
        request.session["django_language"] = lang_code
        messages.success(
            request,
            "Language changed to English!"
            if lang_code == "en"
            else "Lingua cambiata in Italiano!",
        )
    return redirect(request.META.get("HTTP_REFERER", "todo_list"))


def welcome_page(request):
    """Initial landing page introducing TaskFlow with start CTA."""
    lang_code = request.session.get("django_language", "en")
    t = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
    total_todos = Todo.objects.filter(is_deleted=False).count()
    completed_todos = Todo.objects.filter(is_deleted=False, done=True).count()
    return render(
        request,
        "todos/welcome.html",
        {
            "lang_code": lang_code,
            "t": t,
            "total_todos": total_todos,
            "completed_todos": completed_todos,
        },
    )


def todo_list(request):
    lang_code = request.session.get("django_language", "en")
    t = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])

    active_view = request.GET.get("view", "list").strip()
    filter_preset = request.GET.get("filter", "").strip()
    status_filter = request.GET.get("status", "all").strip()
    is_archived_view = filter_preset == "archived" or status_filter == "archived"
    is_trash_view = active_view == "trash"

    # Base queryset for current user
    all_user_todos = _get_user_todos(
        request,
        include_archived=is_archived_view,
        include_deleted=is_trash_view,
    ).prefetch_related("subtasks", "comments__user", "collaborators")
    if is_archived_view:
        all_user_todos = all_user_todos.filter(is_archived=True)

    today = timezone.localdate()
    todos = all_user_todos

    # Tag filter
    tag_filter = request.GET.get("tag", "").strip().lstrip("#")
    if tag_filter:
        todos = todos.filter(tags__icontains=tag_filter)

    # Collect distinct tags
    all_tags = sorted(
        {
            t.strip().lstrip("#")
            for raw in all_user_todos.values_list("tags", flat=True)
            if raw
            for t in raw.split(",")
            if t.strip()
        }
    )

    # In-App Notifications
    unread_notifications_count = 0
    user_notifications = []
    if request.user.is_authenticated:
        user_notifications = Notification.objects.filter(user=request.user)[:8]
        unread_notifications_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

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
    elif filter_preset == "favorite":
        todos = todos.filter(is_favorite=True)

    # Search query
    query = request.GET.get("q", "").strip()
    if query:
        todos = todos.filter(
            Q(title__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__icontains=query)
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

    # Project filter
    project_filter = request.GET.get("project", "").strip()
    if project_filter and project_filter.isdigit():
        todos = todos.filter(project_id=int(project_filter))

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

    # Gamification XP & Level
    user_xp = completed_count * 15
    user_level = 1 + (user_xp // 60)
    level_tier = (
        "Master 👑"
        if user_level >= 4
        else (
            "Pro 🌟"
            if user_level >= 3
            else ("Achiever ⚡" if user_level >= 2 else "Novice 🌱")
        )
    )

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

    # Eisenhower Matrix Quadrants (Active Tasks)
    matrix_active = all_user_todos.filter(done=False)
    three_days_out = today + timedelta(days=3)
    # Quadrant 1: Urgent & Important (High Priority + Due within 3 days or Overdue)
    matrix_q1 = matrix_active.filter(
        priority="high",
        due_date__lte=three_days_out,
    )
    # Quadrant 2: Important, Not Urgent (High/Medium Priority + Due later or no due date)
    matrix_q2 = matrix_active.filter(
        Q(priority="high", due_date__gt=three_days_out)
        | Q(priority="high", due_date__isnull=True)
        | Q(priority="medium", due_date__gt=three_days_out)
        | Q(priority="medium", due_date__isnull=True)
    )
    # Quadrant 3: Urgent, Not Important (Medium/Low Priority + Due within 3 days)
    matrix_q3 = matrix_active.filter(
        Q(priority__in=["medium", "low"]),
        due_date__lte=three_days_out,
    ).exclude(pk__in=matrix_q1.values_list("pk", flat=True))
    # Quadrant 4: Neither (Low Priority, no tight deadline)
    matrix_q4 = matrix_active.filter(
        priority="low",
    ).exclude(pk__in=matrix_q3.values_list("pk", flat=True))

    # Interactive Calendar View computation
    try:
        cal_year = int(request.GET.get("year", today.year))
        cal_month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        cal_year = today.year
        cal_month = today.month

    if cal_month < 1:
        cal_month = 12
        cal_year -= 1
    elif cal_month > 12:
        cal_month = 1
        cal_year += 1

    prev_year, prev_month = (
        (cal_year - 1, 12) if cal_month == 1 else (cal_year, cal_month - 1)
    )
    next_year, next_month = (
        (cal_year + 1, 1) if cal_month == 12 else (cal_year, cal_month + 1)
    )
    cal_month_title = datetime(cal_year, cal_month, 1).strftime("%B %Y")

    cal_matrix = calendar.monthcalendar(cal_year, cal_month)
    calendar_grid = []
    for week in cal_matrix:
        week_cells = []
        for d in week:
            if d == 0:
                week_cells.append(
                    {
                        "day": 0,
                        "date": "",
                        "tasks": [],
                        "events": [],
                        "is_today": False,
                    }
                )
            else:
                c_date = datetime(cal_year, cal_month, d).date()
                date_str = c_date.strftime("%Y-%m-%d")
                day_tasks = all_user_todos.filter(due_date=c_date)
                day_events = CollaborationEvent.objects.filter(event_date=c_date)
                week_cells.append(
                    {
                        "day": d,
                        "date": date_str,
                        "tasks": list(day_tasks),
                        "events": list(day_events),
                        "is_today": c_date == today,
                    }
                )
        calendar_grid.append(week_cells)

    # Analytics View computation
    weekdays_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_counts = {w: 0 for w in weekdays_labels}
    for t_item in all_user_todos.filter(done=True):
        w_name = t_item.updated_at.strftime("%a")
        if w_name in weekday_counts:
            weekday_counts[w_name] += 1
    max_wd = max(weekday_counts.values()) if any(weekday_counts.values()) else 1
    analytics_weekdays = [
        {
            "day": w,
            "count": weekday_counts[w],
            "height": int((weekday_counts[w] / max_wd) * 100) if max_wd else 10,
        }
        for w in weekdays_labels
    ]

    cat_stats = []
    for c in categories:
        c_count = all_user_todos.filter(category=c).count()
        if c_count > 0:
            cat_stats.append({"category": c, "count": c_count})
    cat_stats.sort(key=lambda x: x["count"], reverse=True)

    # Leaderboard View computation
    leaderboard_users = []
    for u in User.objects.all():
        u_completed = Todo.objects.filter(user=u, done=True).count()
        u_xp = u_completed * 15
        u_level = 1 + (u_xp // 60)
        leaderboard_users.append(
            {
                "username": u.username,
                "completed_count": u_completed,
                "xp": u_xp,
                "level": u_level,
            }
        )
    leaderboard_users.sort(key=lambda x: (x["xp"], x["completed_count"]), reverse=True)
    for idx, u_entry in enumerate(leaderboard_users, 1):
        u_entry["rank"] = idx

    # Social & Collaborative Events
    social_activities = SocialActivity.objects.select_related("user")[:25]
    collaborative_events = CollaborationEvent.objects.prefetch_related(
        "participants"
    ).select_related("organizer")[:25]

    # Projects
    projects = Project.objects.all()

    # Timeline Gantt View computation (14-day rolling window)
    timeline_start = today - timedelta(days=2)
    timeline_days = [
        {
            "date": timeline_start + timedelta(days=i),
            "date_str": (timeline_start + timedelta(days=i)).strftime("%Y-%m-%d"),
            "day_num": (timeline_start + timedelta(days=i)).day,
            "weekday": (timeline_start + timedelta(days=i)).strftime("%a"),
            "is_today": (timeline_start + timedelta(days=i)) == today,
        }
        for i in range(14)
    ]
    timeline_tasks = []
    for t_item in all_user_todos.filter(done=False):
        if t_item.due_date:
            offset = (t_item.due_date - timeline_start).days
            clamped_offset = max(0, min(13, offset))
            timeline_tasks.append(
                {
                    "todo": t_item,
                    "offset": clamped_offset,
                    "is_overdue": t_item.due_date < today,
                    "is_today": t_item.due_date == today,
                    "in_window": 0 <= offset <= 13,
                }
            )

    # Habits Tracker & 30-Day Contribution Heat Map
    habits_list = []
    past_30_days = [today - timedelta(days=i) for i in reversed(range(30))]
    all_habits = Habit.objects.prefetch_related("logs").all()
    for h in all_habits:
        completed_dates = set(h.logs.values_list("date", flat=True))
        history = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "day_num": d.day,
                "done": d in completed_dates,
                "is_today": d == today,
            }
            for d in past_30_days
        ]
        completed_past_30 = sum(1 for d in history if d["done"])
        habits_list.append(
            {
                "habit": h,
                "history": history,
                "completed_30": completed_past_30,
                "completion_rate": int((completed_past_30 / 30) * 100),
                "is_done_today": today in completed_dates,
            }
        )

    # Standup Summary data
    standup_completed = all_user_todos.filter(done=True, updated_at__date=today)[:10]
    standup_in_progress = all_user_todos.filter(status="in_progress", done=False)[:10]
    standup_critical = all_user_todos.filter(
        Q(due_date__lt=today) | Q(priority="high"), done=False
    )[:10]

    # Suite 1: Second Brain & Wiki
    wiki_pages = WikiPage.objects.all()
    wiki_categories = sorted(set(w.category for w in wiki_pages if w.category))
    wiki_all_tags = sorted(set(t for w in wiki_pages for t in w.tag_list()))

    # Suite 2: Finance Tracker & Budget
    transactions = Transaction.objects.all()[:100]
    savings_goals = SavingsGoal.objects.all()
    total_income = sum(
        (t.amount for t in transactions if t.transaction_type == "income"),
        Decimal("0.00"),
    )
    total_expense = sum(
        (t.amount for t in transactions if t.transaction_type == "expense"),
        Decimal("0.00"),
    )
    net_balance = total_income - total_expense
    monthly_budget = Decimal("1500.00")
    budget_spent_percent = (
        min(100, int((total_expense / monthly_budget) * 100))
        if monthly_budget > 0
        else 0
    )
    budget_remaining = max(Decimal("0.00"), monthly_budget - total_expense)

    # Suite 3: Daily Journal & Mood Tracker
    all_journal_entries = JournalEntry.objects.all()
    journal_entries = all_journal_entries[:30]
    today_journal = JournalEntry.objects.filter(date=today).first()
    mood_counts = {
        "radiant": all_journal_entries.filter(mood="radiant").count(),
        "energetic": all_journal_entries.filter(mood="energetic").count(),
        "calm": all_journal_entries.filter(mood="calm").count(),
        "tired": all_journal_entries.filter(mood="tired").count(),
        "stressed": all_journal_entries.filter(mood="stressed").count(),
    }

    # Suite 4: Media & Bookshelf Tracker
    media_items = MediaItem.objects.all()
    media_want = media_items.filter(status="want")
    media_progress = media_items.filter(status="progress")
    media_completed = media_items.filter(status="completed")
    media_completed_this_year = media_completed.filter(
        completed_at__year=today.year
    ).count()
    media_yearly_goal = 20
    media_goal_percent = min(
        100, int((media_completed_this_year / media_yearly_goal) * 100)
    )

    # Suite 5: Productivity RPG
    rpg_profile, _ = UserProfileRPG.objects.get_or_create(
        user=request.user if request.user.is_authenticated else None
    )
    rpg_rewards = RpgReward.objects.all()

    context = {
        "wiki_pages": wiki_pages,
        "wiki_categories": wiki_categories,
        "wiki_all_tags": wiki_all_tags,
        "transactions": transactions,
        "savings_goals": savings_goals,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "monthly_budget": monthly_budget,
        "budget_spent_percent": budget_spent_percent,
        "budget_remaining": budget_remaining,
        "journal_entries": journal_entries,
        "today_journal": today_journal,
        "mood_counts": mood_counts,
        "media_items": media_items,
        "media_want": media_want,
        "media_progress": media_progress,
        "media_completed": media_completed,
        "media_completed_this_year": media_completed_this_year,
        "media_yearly_goal": media_yearly_goal,
        "media_goal_percent": media_goal_percent,
        "rpg_profile": rpg_profile,
        "rpg_rewards": rpg_rewards,
        "projects": projects,
        "current_project": project_filter,
        "timeline_days": timeline_days,
        "timeline_tasks": timeline_tasks,
        "habits_data": habits_list,
        "standup_completed": standup_completed,
        "standup_in_progress": standup_in_progress,
        "standup_critical": standup_critical,
        "todos": todos,
        "active_view": active_view,
        "lang_code": lang_code,
        "t": t,
        "total_count": total_count,
        "completed_count": completed_count,
        "active_count": active_count,
        "progress_percent": progress_percent,
        "pinned_count": pinned_count,
        "overdue_count": overdue_count,
        "today_count": today_count,
        "formatted_workload": formatted_workload,
        "user_xp": user_xp,
        "user_level": user_level,
        "level_tier": level_tier,
        "categories": categories,
        "all_tags": all_tags,
        "current_tag": tag_filter,
        "cal_year": cal_year,
        "cal_month": cal_month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "cal_month_title": cal_month_title,
        "calendar_grid": calendar_grid,
        "analytics_weekdays": analytics_weekdays,
        "cat_stats": cat_stats,
        "leaderboard_users": leaderboard_users,
        "user_notifications": user_notifications,
        "unread_notifications_count": unread_notifications_count,
        "current_query": query,
        "current_status": status_filter,
        "current_category": category_filter,
        "current_priority": priority_filter,
        "current_sort": sort_by,
        "current_filter": filter_preset,
        "is_archived_view": is_archived_view,
        "is_trash_view": is_trash_view,
        "today_str": today.strftime("%Y-%m-%d"),
        "kanban_todo": kanban_todo,
        "kanban_in_progress": kanban_in_progress,
        "kanban_done": kanban_done,
        "matrix_q1": matrix_q1,
        "matrix_q2": matrix_q2,
        "matrix_q3": matrix_q3,
        "matrix_q4": matrix_q4,
        "social_activities": social_activities,
        "collaborative_events": collaborative_events,
    }
    return render(request, "todos/todo_list.html", context)


@require_POST
def todo_add(request):
    title = request.POST.get("title", "").strip()
    category = request.POST.get("category", "").strip()
    tags = request.POST.get("tags", "").strip()
    priority = request.POST.get("priority", "medium").strip()
    energy_level = request.POST.get("energy_level", "medium").strip()
    recurrence = request.POST.get("recurrence", "none").strip()
    due_date_str = request.POST.get("due_date", "").strip()
    description = request.POST.get("description", "").strip()
    estimated_minutes_str = request.POST.get("estimated_minutes", "0").strip()
    is_pinned = request.POST.get("is_pinned") == "on"

    if priority not in ["low", "medium", "high"]:
        priority = "medium"
    if energy_level not in ["low", "medium", "high"]:
        energy_level = "medium"
    if recurrence not in ["none", "daily", "weekly", "monthly"]:
        recurrence = "none"

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

    project_id = request.POST.get("project", "").strip()
    project = None
    if project_id and project_id.isdigit():
        project = Project.objects.filter(pk=int(project_id)).first()

    if title:
        user = request.user if request.user.is_authenticated else None
        Todo.objects.create(
            user=user,
            title=title,
            category=category,
            project=project,
            tags=tags,
            priority=priority,
            energy_level=energy_level,
            recurrence=recurrence,
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
    tags = request.POST.get("tags", "").strip()
    priority = request.POST.get("priority", "medium").strip()
    energy_level = request.POST.get("energy_level", "medium").strip()
    recurrence = request.POST.get("recurrence", "none").strip()
    due_date_str = request.POST.get("due_date", "").strip()
    description = request.POST.get("description", "").strip()
    estimated_minutes_str = request.POST.get("estimated_minutes", "0").strip()
    is_pinned = request.POST.get("is_pinned") == "on"

    project_id = request.POST.get("project", "").strip()
    if project_id and project_id.isdigit():
        todo.project = Project.objects.filter(pk=int(project_id)).first()
    elif "project" in request.POST:
        todo.project = None

    actual_minutes_str = request.POST.get("actual_minutes")
    if actual_minutes_str is not None:
        try:
            todo.actual_minutes = max(0, int(actual_minutes_str))
        except ValueError:
            pass

    if priority in ["low", "medium", "high"]:
        todo.priority = priority
    if energy_level in ["low", "medium", "high"]:
        todo.energy_level = energy_level
    if recurrence in ["none", "daily", "weekly", "monthly"]:
        todo.recurrence = recurrence

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
    todo.tags = tags
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
def todo_favorite(request, pk):
    """Toggle starred/favorite state of a task."""
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    todo.is_favorite = not todo.is_favorite
    todo.save()
    status_msg = "starred as favorite ★" if todo.is_favorite else "unstarred"
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
def todo_trash(request, pk):
    """Move task to trash bin (soft-delete)."""
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    todo.is_deleted = True
    todo.save()
    messages.success(request, f'Moved "{todo.title}" to Trash bin.')
    return redirect("todo_list")


@require_POST
def todo_restore(request, pk):
    """Restore task from trash bin."""
    todo = get_object_or_404(Todo, pk=pk)
    if todo.user and todo.user != request.user:
        raise Http404("Todo not found")

    todo.is_deleted = False
    todo.save()
    messages.success(request, f'Restored "{todo.title}" from Trash bin.')
    return redirect(f"{reverse('todo_list')}?view=trash")


@require_POST
def todo_empty_trash(request):
    """Permanently delete all tasks in trash for this user."""
    trashed = _get_user_todos(request, include_deleted=True)
    count = trashed.count()
    trashed.delete()
    messages.success(request, f"Permanently deleted {count} trashed task(s).")
    return redirect(f"{reverse('todo_list')}?view=trash")


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
        _award_rpg_xp(request, xp=15, coins=5, stat="discipline")
        if request.user.is_authenticated:
            SocialActivity.objects.create(
                user=request.user,
                message=f'completed the task: "{todo.title}"! ✅',
            )
        # Recurring task automation: spawn next occurrence!
        if todo.recurrence != "none":
            next_due = None
            if todo.due_date:
                if todo.recurrence == "daily":
                    next_due = todo.due_date + timedelta(days=1)
                elif todo.recurrence == "weekly":
                    next_due = todo.due_date + timedelta(days=7)
                elif todo.recurrence == "monthly":
                    next_due = todo.due_date + timedelta(days=30)

            Todo.objects.create(
                user=todo.user,
                title=todo.title,
                category=todo.category,
                priority=todo.priority,
                energy_level=todo.energy_level,
                recurrence=todo.recurrence,
                due_date=next_due,
                description=todo.description,
                estimated_minutes=todo.estimated_minutes,
                is_pinned=todo.is_pinned,
                done=False,
                status="todo",
            )
            messages.info(
                request,
                f'Recurring task: next cycle of "{todo.title}" scheduled!',
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
    Notification.objects.create(
        user=target_user,
        message=f'@{request.user.username} shared task "{todo.title}" with you! 👥',
        link=f"{reverse('todo_list')}?view=list#task-{todo.id}",
    )
    messages.success(request, f"Task shared with @{target_user.username} successfully!")
    return redirect("todo_list")


@require_POST
def task_comment_add(request, pk):
    """Add a discussion comment to a task."""
    todo = get_object_or_404(Todo, pk=pk)
    if (
        todo.user
        and todo.user != request.user
        and not todo.collaborators.filter(pk=request.user.pk).exists()
    ):
        raise Http404("Todo not found")

    text = request.POST.get("text", "").strip()
    if text and request.user.is_authenticated:
        TaskComment.objects.create(todo=todo, user=request.user, text=text)
        # Notify owner if commenter is not owner
        if todo.user and todo.user != request.user:
            Notification.objects.create(
                user=todo.user,
                message=f'@{request.user.username} commented on "{todo.title}" 💬',
                link=f"{reverse('todo_list')}?view=list#task-{todo.id}",
            )
        messages.success(request, "Comment posted!")
    return redirect(request.META.get("HTTP_REFERER", "todo_list"))


@require_POST
def notification_clear(request):
    """Mark all notifications as read for current user."""
    if request.user.is_authenticated:
        Notification.objects.filter(user=request.user).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
    return redirect(request.META.get("HTTP_REFERER", "todo_list"))


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
def todo_time_log(request, pk):
    """Log actual time spent on a task."""
    todo = get_object_or_404(Todo, pk=pk)
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
            minutes = int(data.get("minutes", 0))
        else:
            minutes = int(request.POST.get("minutes", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        minutes = 0

    if minutes > 0:
        todo.actual_minutes += minutes
        todo.save(update_fields=["actual_minutes", "updated_at"])

    if (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.content_type == "application/json"
    ):
        return JsonResponse(
            {
                "status": "ok",
                "actual_minutes": todo.actual_minutes,
                "formatted_actual": todo.formatted_actual_duration,
            }
        )

    messages.success(request, f"Registrati {minutes}m su '{todo.title}'.")
    return redirect(request.POST.get("next") or reverse("todo_list"))


@require_POST
def todo_smart_breakdown(request, pk):
    """Generate intelligent subtasks for a task using contextual heuristics."""
    todo = get_object_or_404(Todo, pk=pk)
    title_lower = todo.title.lower()

    if any(k in title_lower for k in ["prep", "stud", "esame", "exam", "corso"]):
        generated_steps = [
            "Raccogli appunti e materiale di studio",
            "Crea schema riassuntivo dei concetti chiave",
            "Esegui esercizi pratici e simulazione",
            "Ripasso finale e verifica dubbi",
        ]
    elif any(
        k in title_lower
        for k in ["progetto", "project", "app", "sito", "code", "svilupp"]
    ):
        generated_steps = [
            "Definisci requisiti e architettura iniziale",
            "Implementa logica principale e modelli dati",
            "Disegna e rifinisci interfaccia utente",
            "Test funzionali, rifinitura e rilascio",
        ]
    elif any(k in title_lower for k in ["viaggio", "trip", "vacanza", "volo", "hotel"]):
        generated_steps = [
            "Verifica documenti e prenotazioni",
            "Prepara valigia e lista accessori essenziali",
            "Pianifica itinerario e spostamenti",
            "Conferma check-in e orari di partenza",
        ]
    elif any(k in title_lower for k in ["puliz", "clean", "casa", "ordin"]):
        generated_steps = [
            "Riordina oggetti fuori posto nelle stanze",
            "Pulisci e igienizza le superfici principali",
            "Aspira e lava i pavimenti",
            "Porta fuori spazzatura e differenziata",
        ]
    elif any(k in title_lower for k in ["spesa", "buy", "compra", "market", "negozio"]):
        generated_steps = [
            "Controlla dispensa e frigorifero",
            "Scrivi lista ingredienti per categoria",
            "Acquista prodotti freschi e alimentari",
            "Riponi e organizza la dispensa",
        ]
    else:
        generated_steps = [
            f"Fase 1: Analisi e preparazione per {todo.title[:30]}",
            "Fase 2: Esecuzione delle attività principali",
            "Fase 3: Revisione dettagli e controllo qualità",
            "Fase 4: Conclusione e archiviazione finale",
        ]

    for step in generated_steps:
        SubTask.objects.create(todo=todo, title=step, done=False)

    messages.success(
        request, f"Generati {len(generated_steps)} sotto-obiettivi con Assistente AI!"
    )
    return redirect(request.POST.get("next") or reverse("todo_list"))


@require_POST
def project_add(request):
    """Create a new project workspace."""
    name = request.POST.get("name", "").strip()
    icon = request.POST.get("icon", "📁").strip() or "📁"
    color = request.POST.get("color", "#a855f7").strip() or "#a855f7"
    if name:
        user = request.user if request.user.is_authenticated else None
        Project.objects.create(user=user, name=name, icon=icon, color=color)
        messages.success(request, f"Progetto '{name}' creato con successo!")
    return redirect(request.POST.get("next") or reverse("todo_list"))


@require_POST
def project_delete(request, pk):
    """Delete a project workspace."""
    project = get_object_or_404(Project, pk=pk)
    name = project.name
    project.delete()
    messages.success(request, f"Progetto '{name}' eliminato.")
    return redirect(reverse("todo_list"))


@require_POST
def habit_add(request):
    """Create a new habit."""
    name = request.POST.get("name", "").strip()
    if name:
        user = request.user if request.user.is_authenticated else None
        Habit.objects.create(user=user, name=name)
        messages.success(request, f"Abitudine '{name}' creata!")
    return redirect(reverse("todo_list") + "?view=habits")


@require_POST
def habit_toggle(request, pk):
    """Toggle a habit completion for today and update streak."""
    habit = get_object_or_404(Habit, pk=pk)
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    log = HabitLog.objects.filter(habit=habit, date=today).first()
    if log:
        log.delete()
        prev_log = HabitLog.objects.filter(habit=habit).order_by("-date").first()
        habit.last_completed_date = prev_log.date if prev_log else None
        habit.streak_count = max(0, habit.streak_count - 1)
        habit.save()
        messages.info(request, f"Abitudine '{habit.name}' annullata per oggi.")
    else:
        HabitLog.objects.create(habit=habit, date=today)
        if habit.last_completed_date == yesterday:
            habit.streak_count += 1
        elif habit.last_completed_date == today:
            pass
        else:
            habit.streak_count = 1
        habit.last_completed_date = today
        habit.save()
        _award_rpg_xp(request, xp=20, coins=8, stat="discipline")
        messages.success(
            request,
            f"🔥 Obiettivo '{habit.name}' completato! Streak: {habit.streak_count} giorni!",
        )
    return redirect(request.POST.get("next") or (reverse("todo_list") + "?view=habits"))


@require_POST
def habit_delete(request, pk):
    """Delete a habit."""
    habit = get_object_or_404(Habit, pk=pk)
    name = habit.name
    habit.delete()
    messages.success(request, f"Abitudine '{name}' rimossa.")
    return redirect(reverse("todo_list") + "?view=habits")


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
        return redirect(f"{reverse('todo_list')}?view=events")

    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid event date format.")
        return redirect(f"{reverse('todo_list')}?view=events")

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
    return redirect(f"{reverse('todo_list')}?view=events")


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
    return redirect(f"{reverse('todo_list')}?view=events")


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
    return redirect(f"{reverse('todo_list')}?view=social")


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
        energy_level=todo.energy_level,
        recurrence=todo.recurrence,
        due_date=todo.due_date,
        description=todo.description,
        estimated_minutes=todo.estimated_minutes,
        is_pinned=todo.is_pinned,
        done=False,
    )
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
            "recurrence": t.recurrence,
            "energy_level": t.energy_level,
            "is_favorite": t.is_favorite,
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
            "Recurrence",
            "Energy Level",
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
                t.recurrence,
                t.energy_level,
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

            energy_level = item.get("energy_level", "medium")
            if energy_level not in ["low", "medium", "high"]:
                energy_level = "medium"

            recurrence = item.get("recurrence", "none")
            if recurrence not in ["none", "daily", "weekly", "monthly"]:
                recurrence = "none"

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
                energy_level=energy_level,
                recurrence=recurrence,
                due_date=due_date,
                estimated_minutes=est,
                is_pinned=bool(item.get("is_pinned", False)),
                is_favorite=bool(item.get("is_favorite", False)),
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
            "recurrence": t.recurrence,
            "energy_level": t.energy_level,
            "is_favorite": t.is_favorite,
            "tags": t.tags,
            "due_date": str(t.due_date) if t.due_date else None,
            "estimated_minutes": t.estimated_minutes,
            "is_pinned": t.is_pinned,
            "done": t.done,
            "subtasks_count": t.total_subtasks_count,
            "completed_subtasks": t.completed_subtasks_count,
            "comments_count": t.comments.count(),
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


# ==========================================
# SUITE 1: SECOND BRAIN & WIKI VIEWS
# ==========================================


@require_POST
def wiki_add(request):
    title = request.POST.get("title", "").strip()
    if title:
        user = request.user if request.user.is_authenticated else None
        category = request.POST.get("category", "Generale").strip() or "Generale"
        tags = request.POST.get("tags", "").strip()
        content = request.POST.get("content", "").strip()
        slug = slugify(title)
        WikiPage.objects.create(
            user=user,
            title=title,
            slug=slug,
            category=category,
            tags=tags,
            content=content,
        )
        _award_rpg_xp(request, xp=25, coins=10, stat="creativity")
        messages.success(request, f"Nota '{title}' salvata nel Second Brain! 🧠")
    return redirect(reverse("todo_list") + "?view=wiki")


@require_POST
def wiki_edit(request, pk):
    page = get_object_or_404(WikiPage, pk=pk)
    title = request.POST.get("title", "").strip()
    if title:
        page.title = title
        page.slug = slugify(title)
        page.category = request.POST.get("category", "Generale").strip() or "Generale"
        page.tags = request.POST.get("tags", "").strip()
        page.content = request.POST.get("content", "").strip()
        page.save()
        messages.success(request, f"Nota '{page.title}' aggiornata!")
    return redirect(reverse("todo_list") + "?view=wiki")


@require_POST
def wiki_delete(request, pk):
    page = get_object_or_404(WikiPage, pk=pk)
    title = page.title
    page.delete()
    messages.success(request, f"Nota '{title}' eliminata.")
    return redirect(reverse("todo_list") + "?view=wiki")


# ==========================================
# SUITE 2: FINANCE & BUDGET VIEWS
# ==========================================


@require_POST
def transaction_add(request):
    title = request.POST.get("title", "").strip()
    amount_raw = request.POST.get("amount", "0").replace(",", ".").strip()
    try:
        amount = Decimal(amount_raw)
    except Exception:
        amount = Decimal("0.00")
    if title and amount > 0:
        user = request.user if request.user.is_authenticated else None
        ttype = request.POST.get("transaction_type", "expense")
        category = request.POST.get("category", "Altro").strip() or "Altro"
        notes = request.POST.get("notes", "").strip()
        date_raw = request.POST.get("date", "").strip()
        try:
            tx_date = (
                datetime.strptime(date_raw, "%Y-%m-%d").date()
                if date_raw
                else timezone.localdate()
            )
        except ValueError:
            tx_date = timezone.localdate()
        Transaction.objects.create(
            user=user,
            title=title,
            amount=amount,
            transaction_type=ttype,
            category=category,
            date=tx_date,
            notes=notes,
        )
        messages.success(request, f"Transazione '{title}' registrata con successo!")
    return redirect(reverse("todo_list") + "?view=finance")


@require_POST
def transaction_delete(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)
    title = tx.title
    tx.delete()
    messages.success(request, f"Transazione '{title}' rimossa.")
    return redirect(reverse("todo_list") + "?view=finance")


@require_POST
def savings_add(request):
    title = request.POST.get("title", "").strip()
    target_raw = request.POST.get("target_amount", "0").replace(",", ".").strip()
    current_raw = request.POST.get("current_amount", "0").replace(",", ".").strip()
    try:
        target_amount = Decimal(target_raw)
        current_amount = Decimal(current_raw)
    except Exception:
        target_amount, current_amount = Decimal("0.00"), Decimal("0.00")
    if title and target_amount > 0:
        user = request.user if request.user.is_authenticated else None
        icon = request.POST.get("icon", "🎯").strip() or "🎯"
        date_raw = request.POST.get("target_date", "").strip()
        try:
            target_date = (
                datetime.strptime(date_raw, "%Y-%m-%d").date() if date_raw else None
            )
        except ValueError:
            target_date = None
        SavingsGoal.objects.create(
            user=user,
            title=title,
            target_amount=target_amount,
            current_amount=current_amount,
            icon=icon,
            target_date=target_date,
        )
        messages.success(request, f"Obiettivo di risparmio '{title}' creato!")
    return redirect(reverse("todo_list") + "?view=finance")


@require_POST
def savings_contribute(request, pk):
    goal = get_object_or_404(SavingsGoal, pk=pk)
    amount_raw = request.POST.get("amount", "0").replace(",", ".").strip()
    try:
        amount = Decimal(amount_raw)
    except Exception:
        amount = Decimal("0.00")
    if amount > 0:
        goal.current_amount += amount
        goal.save()
        _award_rpg_xp(request, xp=15, coins=5, stat="discipline")
        messages.success(
            request,
            f"Versati €{amount} per '{goal.title}'! Avanzamento: {goal.percent_complete}%",
        )
    return redirect(reverse("todo_list") + "?view=finance")


@require_POST
def savings_delete(request, pk):
    goal = get_object_or_404(SavingsGoal, pk=pk)
    title = goal.title
    goal.delete()
    messages.success(request, f"Obiettivo '{title}' eliminato.")
    return redirect(reverse("todo_list") + "?view=finance")


# ==========================================
# SUITE 3: DAILY JOURNAL & MOOD VIEWS
# ==========================================


@require_POST
def journal_add(request):
    date_raw = request.POST.get("date", "").strip()
    try:
        j_date = (
            datetime.strptime(date_raw, "%Y-%m-%d").date()
            if date_raw
            else timezone.localdate()
        )
    except ValueError:
        j_date = timezone.localdate()
    user = request.user if request.user.is_authenticated else None
    mood = request.POST.get("mood", "calm").strip() or "calm"
    weather = request.POST.get("weather", "☀️").strip() or "☀️"
    gratitude_1 = request.POST.get("gratitude_1", "").strip()
    gratitude_2 = request.POST.get("gratitude_2", "").strip()
    gratitude_3 = request.POST.get("gratitude_3", "").strip()
    content = request.POST.get("content", "").strip()

    entry = JournalEntry.objects.filter(user=user, date=j_date).first()
    if entry:
        entry.mood = mood
        entry.weather = weather
        entry.gratitude_1 = gratitude_1
        entry.gratitude_2 = gratitude_2
        entry.gratitude_3 = gratitude_3
        entry.content = content
        entry.save()
        messages.success(request, f"Diario del {j_date} aggiornato!")
    else:
        JournalEntry.objects.create(
            user=user,
            date=j_date,
            mood=mood,
            weather=weather,
            gratitude_1=gratitude_1,
            gratitude_2=gratitude_2,
            gratitude_3=gratitude_3,
            content=content,
        )
        _award_rpg_xp(request, xp=30, coins=10, stat="vitality")
        messages.success(request, f"Pagina di diario salvata per il {j_date}! 📖")
    return redirect(reverse("todo_list") + "?view=journal")


@require_POST
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk)
    entry.delete()
    messages.success(request, "Pagina di diario rimossa.")
    return redirect(reverse("todo_list") + "?view=journal")


# ==========================================
# SUITE 4: BOOKSHELF & MEDIA VIEWS
# ==========================================


@require_POST
def media_add(request):
    title = request.POST.get("title", "").strip()
    if title:
        user = request.user if request.user.is_authenticated else None
        creator = request.POST.get("creator", "").strip()
        media_type = request.POST.get("media_type", "book").strip() or "book"
        status = request.POST.get("status", "want").strip() or "want"
        try:
            rating = max(1, min(5, int(request.POST.get("rating", "5"))))
        except (ValueError, TypeError):
            rating = 5
        review = request.POST.get("review", "").strip()
        icon = request.POST.get("icon", "📚").strip() or "📚"
        completed_at = timezone.localdate() if status == "completed" else None
        MediaItem.objects.create(
            user=user,
            title=title,
            creator=creator,
            media_type=media_type,
            status=status,
            rating=rating,
            review=review,
            icon=icon,
            completed_at=completed_at,
        )
        _award_rpg_xp(request, xp=20, coins=5, stat="creativity")
        messages.success(request, f"'{title}' aggiunto alla tua libreria! 📚")
    return redirect(reverse("todo_list") + "?view=media")


@require_POST
def media_status_update(request, pk):
    item = get_object_or_404(MediaItem, pk=pk)
    new_status = request.POST.get("status", item.status).strip()
    item.status = new_status
    if new_status == "completed" and not item.completed_at:
        item.completed_at = timezone.localdate()
        _award_rpg_xp(request, xp=40, coins=15, stat="focus")
        messages.success(
            request,
            f"Complimenti! Hai completato '{item.title}'! 🎉 (+40 XP)",
        )
    rating_raw = request.POST.get("rating")
    if rating_raw:
        try:
            item.rating = max(1, min(5, int(rating_raw)))
        except (ValueError, TypeError):
            pass
    item.save()
    return redirect(reverse("todo_list") + "?view=media")


@require_POST
def media_delete(request, pk):
    item = get_object_or_404(MediaItem, pk=pk)
    title = item.title
    item.delete()
    messages.success(request, f"'{title}' rimosso dalla libreria.")
    return redirect(reverse("todo_list") + "?view=media")


# ==========================================
# SUITE 5: PRODUCTIVITY RPG VIEWS
# ==========================================


@require_POST
def rpg_reward_add(request):
    title = request.POST.get("title", "").strip()
    try:
        cost = max(1, int(request.POST.get("cost_coins", "30")))
    except (ValueError, TypeError):
        cost = 30
    icon = request.POST.get("icon", "🎁").strip() or "🎁"
    if title:
        user = request.user if request.user.is_authenticated else None
        RpgReward.objects.create(
            user=user,
            title=title,
            cost_coins=cost,
            icon=icon,
        )
        messages.success(request, f"Nuova ricompensa '{title}' aggiunta al Negozio! 🏪")
    return redirect(reverse("todo_list") + "?view=rpg")


@require_POST
def rpg_reward_redeem(request, pk):
    reward = get_object_or_404(RpgReward, pk=pk)
    user = request.user if request.user.is_authenticated else None
    profile, _ = UserProfileRPG.objects.get_or_create(user=user)
    if profile.coins >= reward.cost_coins:
        profile.coins -= reward.cost_coins
        profile.save()
        reward.is_redeemed = True
        reward.save()
        messages.success(
            request,
            f"🎉 Ricompensa '{reward.title}' riscattata con successo! Goditi il tuo premio!",
        )
    else:
        messages.error(
            request,
            f"Monete insufficienti! Ti servono {reward.cost_coins} monete (ne hai {profile.coins}).",
        )
    return redirect(reverse("todo_list") + "?view=rpg")


@require_POST
def rpg_reward_delete(request, pk):
    reward = get_object_or_404(RpgReward, pk=pk)
    title = reward.title
    reward.delete()
    messages.success(request, f"Ricompensa '{title}' eliminata.")
    return redirect(reverse("todo_list") + "?view=rpg")


# ==========================================
# SUITE 7: AI PROBLEM SOLVER ENDPOINT
# ==========================================


@require_POST
def api_ai_solve(request):
    """Analyze a problem and return structured diagnosis, actionable strategies, and suggested tasks."""
    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        body = {}
    problem = (body.get("problem") or request.POST.get("problem", "")).strip()

    if not problem:
        return JsonResponse(
            {"status": "error", "message": "Descrivi un problema per procedere."},
            status=400,
        )

    p_lower = problem.lower()

    if any(
        k in p_lower
        for k in ["procrastin", "rimand", "blocc", "voglia", "difficil", "inizia"]
    ):
        diagnosis = (
            "La procrastinazione è spesso una risposta all'ansia da prestazione o alla mole "
            "percepita dell'obiettivo. Il cervello cerca sollievo immediato rimandando."
        )
        strategies = [
            "Applica la 'Regola dei 2 Minuti': prometti a te stesso di lavorare al compito solo per 120 secondi.",
            "Riduci l'attrito iniziale: prepara l'ambiente rimuovendo distrazioni e aprendo solo il materiale essenziale.",
            "Elimina il perfezionismo: la prima bozza può essere imperfetta, l'importante è far partire lo slancio.",
        ]
        tasks = [
            {
                "title": f"Avvio rapido 2m: prima bozza per {problem[:30]}",
                "priority": "high",
                "estimated_minutes": 10,
            },
            {
                "title": "Sessione Pomodoro (25m) focalizzata",
                "priority": "high",
                "estimated_minutes": 25,
            },
            {
                "title": "Revisione e festeggiamento del traguardo",
                "priority": "medium",
                "estimated_minutes": 10,
            },
        ]
    elif any(
        k in p_lower
        for k in [
            "tempo",
            "tropp",
            "scadenz",
            "organizz",
            "giornat",
            "agenda",
            "ritard",
        ]
    ):
        diagnosis = (
            "Il sovraccarico cognitivo nasce dal trattare tutti gli impegni con la stessa urgenza. "
            "Quando tutto è prioritario, nulla lo è veramente."
        )
        strategies = [
            "Applica la Matrice di Eisenhower: isola i 2 compiti che hanno il massimo impatto oggi.",
            "Fai 'Time Blocking': assegna fasce orarie fisse invece di saltare continuamente da un'attività all'altra.",
            "Impara a dire di no o a delegare ciò che non rientra nei tuoi 3 obiettivi centrali.",
        ]
        tasks = [
            {
                "title": f"Isolare i 3 compiti chiave per: {problem[:30]}",
                "priority": "urgent",
                "estimated_minutes": 15,
            },
            {
                "title": "Blocco di concentrazione profonda (45 min)",
                "priority": "high",
                "estimated_minutes": 45,
            },
            {
                "title": "Chiusura ordinata attività aperte",
                "priority": "medium",
                "estimated_minutes": 15,
            },
        ]
    elif any(
        k in p_lower
        for k in ["sold", "spend", "spes", "risparmi", "budget", "finanz", "cost"]
    ):
        diagnosis = (
            "Le spese fuori controllo derivano spesso da piccole 'fughe invisibili' quotidiane che "
            "si accumulano nel corso delle settimane."
        )
        strategies = [
            "Traccia ogni singola uscita per 7 giorni per identificare il vero punto di perdita del budget.",
            "Applica la regola delle 48 ore: attendi due giorni prima di acquistare qualcosa di non essenziale.",
            "Automatizza il risparmio: alloca subito a inizio mese una quota fissa nel tuo salvadanaio digitale.",
        ]
        tasks = [
            {
                "title": f"Controllo spese e abbonamenti ({problem[:25]})",
                "priority": "high",
                "estimated_minutes": 20,
            },
            {
                "title": "Impostare limite spesa settimanale nel Finance Tracker",
                "priority": "high",
                "estimated_minutes": 15,
            },
            {
                "title": "Versamento simbolico di 15€ nel salvadanaio",
                "priority": "medium",
                "estimated_minutes": 5,
            },
        ]
    elif any(
        k in p_lower
        for k in ["ansia", "stress", "stanc", "dorm", "paura", "esaurit", "ripos"]
    ):
        diagnosis = (
            "Il sistema nervoso è in sovraccarico di stimoli. Forzare senza pause adeguate genera "
            "rendimenti decrescenti e affaticamento decisionale."
        )
        strategies = [
            "Effettua una sessione di respirazione quadrata (Box Breathing) di 3 minuti nell'Oasi Sonora.",
            "Fai un 'Brain Dump' nel Diario Personale: svuota tutti i pensieri per liberare spazio mentale.",
            "Stacca dagli schermi ed effettua una camminata di 10 minuti per rigenerare la lucidità.",
        ]
        tasks = [
            {
                "title": "3 minuti di respirazione profonda nell'Oasi Sonora",
                "priority": "urgent",
                "estimated_minutes": 5,
            },
            {
                "title": f"Scrivere nel Diario i pensieri su: {problem[:30]}",
                "priority": "high",
                "estimated_minutes": 15,
            },
            {
                "title": "Pausa attiva rigenerante all'aperto",
                "priority": "medium",
                "estimated_minutes": 15,
            },
        ]
    elif any(
        k in p_lower
        for k in [
            "studi",
            "esam",
            "libri",
            "ripass",
            "memor",
            "tesi",
            "scuola",
            "universit",
        ]
    ):
        diagnosis = (
            "La rilettura passiva è inefficiente. Il vero apprendimento avviene tramite recupero "
            "attivo (Active Recall) e scomposizione dei capitoli in concetti chiave."
        )
        strategies = [
            "Crea una scheda di sintesi nel Second Brain / Wiki con domande chiave e collegamenti.",
            "Spiega il concetto ad alta voce come se dovessi insegnarlo (Tecnica di Feynman).",
            "Alterna blocchi da 25 minuti di studio focalizzato a 5 minuti di recupero.",
        ]
        tasks = [
            {
                "title": f"Mappa concettuale nella Wiki per: {problem[:30]}",
                "priority": "high",
                "estimated_minutes": 25,
            },
            {
                "title": "Ripetizione attiva (Active Recall) a libro chiuso",
                "priority": "high",
                "estimated_minutes": 30,
            },
            {
                "title": "Autovalutazione con 5 domande di verifica",
                "priority": "medium",
                "estimated_minutes": 15,
            },
        ]
    else:
        diagnosis = (
            "Ogni problema complesso sembra insormontabile solo finché rimane un blocco unico. "
            "Decomponendolo in unità minime azionabili, la resistenza mentale scompare."
        )
        strategies = [
            "Scomponi il macro-obiettivo nella più piccola azione fisica eseguibile adesso.",
            "Definisci chiaramente il criterio di successo ('Come saprò esattamente quando è completato?').",
            "Imposta una scadenza realistica e celebra il completamento per alimentare la motivazione.",
        ]
        tasks = [
            {
                "title": f"Fase 1: Preparazione e ricerca per {problem[:30]}",
                "priority": "high",
                "estimated_minutes": 20,
            },
            {
                "title": "Fase 2: Esecuzione operativa del primo blocco",
                "priority": "urgent",
                "estimated_minutes": 35,
            },
            {
                "title": "Fase 3: Revisione finale e chiusura",
                "priority": "medium",
                "estimated_minutes": 15,
            },
        ]

    return JsonResponse(
        {
            "status": "ok",
            "problem": problem,
            "diagnosis": diagnosis,
            "strategies": strategies,
            "tasks": tasks,
        }
    )
