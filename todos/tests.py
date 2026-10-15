import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Habit,
    HabitLog,
    JournalEntry,
    MediaItem,
    Notification,
    Project,
    RpgReward,
    SavingsGoal,
    SubTask,
    TaskComment,
    Todo,
    Transaction,
    UserProfileRPG,
    WikiPage,
)

User = get_user_model()


class TodoTests(TestCase):
    def test_list_page_loads(self):
        response = self.client.get(reverse("todo_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nothing to do yet")

    def test_add_a_todo_with_metadata(self):
        self.client.post(
            reverse("todo_add"),
            {
                "title": "Buy groceries",
                "category": "Home",
                "priority": "high",
                "due_date": "2026-10-15",
                "description": "Apples, Milk, Bread",
                "estimated_minutes": "45",
                "is_pinned": "on",
            },
        )
        todo = Todo.objects.get()
        self.assertEqual(todo.title, "Buy groceries")
        self.assertEqual(todo.category, "Home")
        self.assertEqual(todo.priority, "high")
        self.assertEqual(str(todo.due_date), "2026-10-15")
        self.assertEqual(todo.description, "Apples, Milk, Bread")
        self.assertEqual(todo.estimated_minutes, 45)
        self.assertTrue(todo.is_pinned)

    def test_empty_title_is_not_added(self):
        self.client.post(reverse("todo_add"), {"title": "   "})
        self.assertEqual(Todo.objects.count(), 0)

    def test_toggle_marks_done_and_back(self):
        todo = Todo.objects.create(title="Read chapter 3")
        self.client.post(reverse("todo_toggle", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertTrue(todo.done)
        self.client.post(reverse("todo_toggle", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertFalse(todo.done)

    def test_delete_removes_it(self):
        todo = Todo.objects.create(title="Call home")
        self.client.post(reverse("todo_delete", args=[todo.pk]))
        self.assertEqual(Todo.objects.count(), 0)

    def test_duplicate_todo(self):
        todo = Todo.objects.create(
            title="Design landing page",
            category="Work",
            priority="high",
            estimated_minutes=60,
            is_pinned=True,
        )
        self.client.post(reverse("todo_duplicate", args=[todo.pk]))
        self.assertEqual(Todo.objects.count(), 2)
        duplicated = Todo.objects.get(title="Design landing page (Copy)")
        self.assertEqual(duplicated.category, "Work")
        self.assertEqual(duplicated.priority, "high")
        self.assertEqual(duplicated.estimated_minutes, 60)
        self.assertTrue(duplicated.is_pinned)
        self.assertFalse(duplicated.done)

    def test_pin_toggle(self):
        todo = Todo.objects.create(title="Important milestone", is_pinned=False)
        self.client.post(reverse("todo_pin", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertTrue(todo.is_pinned)

        self.client.post(reverse("todo_pin", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertFalse(todo.is_pinned)

    def test_edit_task(self):
        todo = Todo.objects.create(title="Old title", priority="low")
        self.client.post(
            reverse("todo_edit", args=[todo.pk]),
            {
                "title": "Refined title",
                "category": "Design",
                "priority": "high",
                "due_date": "2026-11-01",
                "description": "Updated specs",
                "estimated_minutes": "90",
                "is_pinned": "on",
            },
        )
        todo.refresh_from_db()
        self.assertEqual(todo.title, "Refined title")
        self.assertEqual(todo.category, "Design")
        self.assertEqual(todo.priority, "high")
        self.assertEqual(str(todo.due_date), "2026-11-01")
        self.assertEqual(todo.description, "Updated specs")
        self.assertEqual(todo.estimated_minutes, 90)
        self.assertTrue(todo.is_pinned)

    def test_archive_toggle(self):
        todo = Todo.objects.create(title="Old finished project", is_archived=False)
        self.client.post(reverse("todo_archive", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertTrue(todo.is_archived)

        # By default archived task should not appear in main task list
        res = self.client.get(reverse("todo_list"))
        self.assertNotContains(
            res, '<span class="task-title">Old finished project</span>'
        )

        # But it should appear in archived view
        res_archived = self.client.get(reverse("todo_list") + "?filter=archived")
        self.assertContains(
            res_archived, '<span class="task-title">Old finished project</span>'
        )

    def test_status_filtering(self):
        Todo.objects.create(title="Pending task", done=False)
        Todo.objects.create(title="Finished task", done=True)

        res_active = self.client.get(reverse("todo_list") + "?status=active")
        self.assertContains(res_active, "Pending task")
        self.assertNotContains(res_active, "Finished task")

        res_completed = self.client.get(reverse("todo_list") + "?status=completed")
        self.assertContains(res_completed, "Finished task")
        self.assertNotContains(res_completed, "Pending task")

    def test_search_filtering(self):
        Todo.objects.create(title="Learn Python")
        Todo.objects.create(title="Wash dishes")

        res = self.client.get(reverse("todo_list") + "?q=Python")
        self.assertContains(res, "Learn Python")
        self.assertNotContains(res, "Wash dishes")

    def test_smart_filters_today_and_overdue(self):
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        Todo.objects.create(title="Task for Today", due_date=today)
        Todo.objects.create(title="Overdue Task", due_date=yesterday, done=False)

        res_today = self.client.get(reverse("todo_list") + "?filter=today")
        self.assertContains(res_today, "Task for Today")

        res_overdue = self.client.get(reverse("todo_list") + "?filter=overdue")
        self.assertContains(res_overdue, "Overdue Task")

    def test_bulk_clear_completed(self):
        Todo.objects.create(title="Active 1", done=False)
        Todo.objects.create(title="Done 1", done=True)
        Todo.objects.create(title="Done 2", done=True)

        self.client.post(reverse("todo_clear_completed"))
        self.assertEqual(Todo.objects.count(), 1)
        self.assertEqual(Todo.objects.first().title, "Active 1")

    def test_bulk_mark_all(self):
        Todo.objects.create(title="Task A", done=False)
        Todo.objects.create(title="Task B", done=False)

        self.client.post(reverse("todo_mark_all"))
        self.assertEqual(Todo.objects.filter(done=True).count(), 2)

    def test_export_json(self):
        Todo.objects.create(title="Export me", category="Work")
        res = self.client.get(reverse("todo_export_json"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "application/json")
        self.assertIn("Export me", res.content.decode("utf-8"))

    def test_export_csv(self):
        Todo.objects.create(title="Export CSV item", priority="high")
        res = self.client.get(reverse("todo_export_csv"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/csv")
        self.assertIn("Export CSV item", res.content.decode("utf-8"))

    def test_export_ical(self):
        today = timezone.localdate()
        Todo.objects.create(title="Calendar Sync Task", due_date=today)

        res = self.client.get(reverse("todo_export_ical"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/calendar")
        content = res.content.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertIn("SUMMARY:Calendar Sync Task", content)

    def test_import_json(self):
        tasks_data = [
            {
                "title": "Imported Task 1",
                "category": "Cloud",
                "priority": "high",
                "estimated_minutes": 45,
            },
            {
                "title": "Imported Task 2",
                "category": "Dev",
                "priority": "low",
            },
        ]
        json_file = SimpleUploadedFile(
            "tasks.json",
            json.dumps(tasks_data).encode("utf-8"),
            content_type="application/json",
        )

        res = self.client.post(
            reverse("todo_import_json"),
            {"json_file": json_file},
            follow=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Todo.objects.filter(title="Imported Task 1").exists())
        self.assertTrue(Todo.objects.filter(title="Imported Task 2").exists())

    def test_api_todos_endpoint(self):
        Todo.objects.create(title="API task", estimated_minutes=30)
        res = self.client.get(reverse("api_todos"))
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(len(json_data["todos"]), 1)
        self.assertEqual(json_data["todos"][0]["title"], "API task")
        self.assertEqual(json_data["todos"][0]["estimated_minutes"], 30)

    def test_user_task_isolation(self):
        user_a = User.objects.create_user(username="alice", password="password123")
        user_b = User.objects.create_user(username="bob", password="password123")

        Todo.objects.create(user=user_a, title="Alice task")
        Todo.objects.create(user=user_b, title="Bob task")

        self.client.force_login(user_a)
        res = self.client.get(reverse("todo_list"))
        self.assertContains(res, "Alice task")
        self.assertNotContains(res, "Bob task")

    def test_signup_page_and_creation(self):
        res = self.client.get(reverse("signup"))
        self.assertEqual(res.status_code, 200)

        post_res = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )
        self.assertEqual(post_res.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_subtask_lifecycle(self):
        todo = Todo.objects.create(title="Parent Project")
        # Add subtask
        self.client.post(reverse("subtask_add", args=[todo.pk]), {"title": "Step 1"})
        self.assertEqual(todo.subtasks.count(), 1)
        subtask = todo.subtasks.first()
        self.assertEqual(subtask.title, "Step 1")
        self.assertFalse(subtask.done)

        # Toggle subtask
        self.client.post(reverse("subtask_toggle", args=[subtask.pk]))
        subtask.refresh_from_db()
        self.assertTrue(subtask.done)

        # Delete subtask
        self.client.post(reverse("subtask_delete", args=[subtask.pk]))
        self.assertEqual(todo.subtasks.count(), 0)

    def test_kanban_status_update(self):
        todo = Todo.objects.create(title="Sprint item", status="todo")
        self.client.post(
            reverse("todo_update_status", args=[todo.pk]),
            {"status": "in_progress"},
        )
        todo.refresh_from_db()
        self.assertEqual(todo.status, "in_progress")
        self.assertFalse(todo.done)

        self.client.post(
            reverse("todo_update_status", args=[todo.pk]),
            {"status": "done"},
        )
        todo.refresh_from_db()
        self.assertEqual(todo.status, "done")
        self.assertTrue(todo.done)

    def test_task_sharing(self):
        owner = User.objects.create_user(username="owner", password="password123")
        collaborator = User.objects.create_user(
            username="collab", password="password123"
        )
        todo = Todo.objects.create(user=owner, title="Joint Mission")

        self.client.force_login(owner)
        self.client.post(
            reverse("todo_share", args=[todo.pk]),
            {"username": "collab"},
        )
        self.assertTrue(todo.collaborators.filter(username="collab").exists())

        # Collaborator should see it in their workspace
        self.client.force_login(collaborator)
        res = self.client.get(reverse("todo_list"))
        self.assertContains(res, "Joint Mission")

    def test_collaborative_events(self):
        organizer = User.objects.create_user(username="host", password="password123")
        participant = User.objects.create_user(username="guest", password="password123")
        self.client.force_login(organizer)

        # Create event
        self.client.post(
            reverse("event_create"),
            {
                "title": "Team Hackathon",
                "event_date": "2026-11-20",
                "description": "Building cool apps",
            },
        )
        from .models import CollaborationEvent

        event = CollaborationEvent.objects.get(title="Team Hackathon")
        self.assertEqual(str(event.event_date), "2026-11-20")

        # Join event as participant
        self.client.force_login(participant)
        self.client.post(reverse("event_join", args=[event.pk]))
        self.assertTrue(event.participants.filter(username="guest").exists())

    def test_social_activity_post(self):
        user = User.objects.create_user(username="socialite", password="password123")
        self.client.force_login(user)
        self.client.post(
            reverse("social_post"),
            {"message": "Hello community! Excited to build together."},
        )
        from .models import SocialActivity

        self.assertTrue(
            SocialActivity.objects.filter(
                message="Hello community! Excited to build together."
            ).exists()
        )

    def test_set_language_view(self):
        self.client.get(reverse("set_language", args=["it"]))
        self.assertEqual(self.client.session.get("django_language"), "it")
        res_page = self.client.get(reverse("todo_list"))
        self.assertContains(res_page, "I Miei Compiti")

        self.client.get(reverse("set_language", args=["en"]))
        self.assertEqual(self.client.session.get("django_language"), "en")
        res_page_en = self.client.get(reverse("todo_list"))
        self.assertContains(res_page_en, "My Tasks")

    def test_todo_favorite(self):
        todo = Todo.objects.create(title="VIP Task", is_favorite=False)
        self.client.post(reverse("todo_favorite", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertTrue(todo.is_favorite)

        self.client.post(reverse("todo_favorite", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertFalse(todo.is_favorite)

    def test_todo_trash_and_restore(self):
        todo = Todo.objects.create(title="Obsolete Task")
        self.client.post(reverse("todo_trash", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertTrue(todo.is_deleted)

        # Trashed task should not appear in regular list view
        res = self.client.get(reverse("todo_list"))
        self.assertNotContains(res, '<span class="task-title">Obsolete Task</span>')

        # But it should appear in trash view
        res_trash = self.client.get(reverse("todo_list") + "?view=trash")
        self.assertContains(res_trash, "Obsolete Task")

        # Restore task
        self.client.post(reverse("todo_restore", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertFalse(todo.is_deleted)

    def test_todo_empty_trash(self):
        Todo.objects.create(title="Discarded Forever", is_deleted=True)
        self.assertEqual(Todo.objects.filter(is_deleted=True).count(), 1)
        self.client.post(reverse("todo_empty_trash"))
        self.assertEqual(Todo.objects.filter(is_deleted=True).count(), 0)

    def test_recurring_task_completion(self):
        today = timezone.localdate()
        todo = Todo.objects.create(
            title="Daily Standup",
            recurrence="daily",
            due_date=today,
            done=False,
        )
        self.client.post(reverse("todo_toggle", args=[todo.pk]))
        todo.refresh_from_db()
        self.assertTrue(todo.done)

        # Next recurring task should be created with due date tomorrow
        next_todo = Todo.objects.get(title="Daily Standup", done=False)
        self.assertEqual(next_todo.recurrence, "daily")
        self.assertEqual(next_todo.due_date, today + timedelta(days=1))

    def test_eisenhower_matrix_view(self):
        today = timezone.localdate()
        Todo.objects.create(
            title="Crisis Fire Drill",
            priority="high",
            due_date=today,
            done=False,
        )
        res = self.client.get(reverse("todo_list") + "?view=matrix")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Crisis Fire Drill")

    def test_energy_level_and_recurrence_creation(self):
        self.client.post(
            reverse("todo_add"),
            {
                "title": "Low energy review",
                "energy_level": "low",
                "recurrence": "weekly",
            },
        )
        todo = Todo.objects.get(title="Low energy review")
        self.assertEqual(todo.energy_level, "low")
        self.assertEqual(todo.recurrence, "weekly")

    def test_calendar_view_loads_and_displays_deadlines(self):
        today = timezone.localdate()
        Todo.objects.create(
            title="Calendar Milestone Task",
            due_date=today,
            priority="high",
        )
        res = self.client.get(reverse("todo_list") + "?view=calendar")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Calendar Milestone Task")

    def test_analytics_view_loads(self):
        res = self.client.get(reverse("todo_list") + "?view=analytics")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Completion Velocity")

    def test_leaderboard_view_loads(self):
        res = self.client.get(reverse("todo_list") + "?view=leaderboard")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Leaderboard")

    def test_task_comment_creation_and_notification(self):
        alice = User.objects.create_user(username="alice", password="password123")
        bob = User.objects.create_user(username="bob", password="password123")
        todo = Todo.objects.create(title="Collaborative Spec", user=alice)
        todo.collaborators.add(bob)

        self.client.force_login(bob)
        res = self.client.post(
            reverse("task_comment_add", args=[todo.pk]),
            {"text": "Feedback from Bob on this task."},
        )
        self.assertEqual(res.status_code, 302)
        self.assertTrue(
            TaskComment.objects.filter(
                todo=todo,
                user=bob,
                text="Feedback from Bob on this task.",
            ).exists()
        )
        # Notification created for Alice
        self.assertTrue(
            Notification.objects.filter(
                user=alice,
                message__contains="bob commented on",
            ).exists()
        )

    def test_notification_clear(self):
        alice = User.objects.create_user(username="alice_notif", password="password123")
        Notification.objects.create(
            user=alice,
            message="You have a new update",
            is_read=False,
        )
        self.client.force_login(alice)
        res = self.client.post(reverse("notification_clear"))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            Notification.objects.filter(user=alice, is_read=False).count(), 0
        )

    def test_tags_filtering_and_list(self):
        todo_tag = Todo.objects.create(
            title="Backend Optimization",
            tags="#backend, #database",
        )
        self.assertIn("backend", todo_tag.tag_list)
        self.assertIn("database", todo_tag.tag_list)

        res_tag = self.client.get(reverse("todo_list") + "?tag=backend")
        self.assertContains(res_tag, "Backend Optimization")

    def test_welcome_page_loads(self):
        res = self.client.get(reverse("welcome"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "TaskFlow Quantum")
        self.assertContains(res, "Start Application")

    def test_time_tracking_and_log(self):
        todo = Todo.objects.create(title="Tracked Task", estimated_minutes=60)
        # Form POST logging 25 minutes
        res1 = self.client.post(
            reverse("todo_time_log", args=[todo.pk]),
            {"minutes": "25"},
        )
        self.assertEqual(res1.status_code, 302)
        todo.refresh_from_db()
        self.assertEqual(todo.actual_minutes, 25)
        self.assertEqual(todo.formatted_actual_duration, "25m")

        # JSON AJAX POST logging 15 minutes
        res2 = self.client.post(
            reverse("todo_time_log", args=[todo.pk]),
            data=json.dumps({"minutes": 15}),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(res2.status_code, 200)
        data = res2.json()
        self.assertEqual(data["actual_minutes"], 40)
        todo.refresh_from_db()
        self.assertEqual(todo.actual_minutes, 40)

    def test_smart_breakdown_ai(self):
        todo = Todo.objects.create(title="Esame di Matematica e studio approfondito")
        res = self.client.post(reverse("todo_smart_breakdown", args=[todo.pk]))
        self.assertEqual(res.status_code, 302)
        subtasks = SubTask.objects.filter(todo=todo)
        self.assertGreaterEqual(subtasks.count(), 3)
        self.assertTrue(
            subtasks.filter(title__icontains="appunti").exists()
            or subtasks.filter(title__icontains="schema").exists()
        )

    def test_project_crud_and_filter(self):
        # Create Project
        res = self.client.post(
            reverse("project_add"),
            {"name": "Frontend Redesign", "icon": "🎨", "color": "#ec4899"},
        )
        self.assertEqual(res.status_code, 302)
        project = Project.objects.get(name="Frontend Redesign")
        self.assertEqual(project.icon, "🎨")
        self.assertEqual(project.color, "#ec4899")

        # Create Task with Project
        self.client.post(
            reverse("todo_add"),
            {"title": "Build UI Components", "project": str(project.id)},
        )
        task = Todo.objects.get(title="Build UI Components")
        self.assertEqual(task.project, project)

        # Filter by Project in List View
        res_list = self.client.get(reverse("todo_list") + f"?project={project.id}")
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, "Build UI Components")

        # Delete Project
        del_res = self.client.post(reverse("project_delete", args=[project.pk]))
        self.assertEqual(del_res.status_code, 302)
        self.assertEqual(Project.objects.filter(pk=project.pk).count(), 0)
        task.refresh_from_db()
        self.assertIsNone(task.project)

    def test_habit_creation_streak_and_toggle(self):
        # Create habit
        res_add = self.client.post(
            reverse("habit_add"),
            {"name": "Morning Meditation"},
        )
        self.assertEqual(res_add.status_code, 302)
        habit = Habit.objects.get(name="Morning Meditation")
        self.assertEqual(habit.streak_count, 0)

        # Toggle habit today -> streak becomes 1
        res_toggle = self.client.post(reverse("habit_toggle", args=[habit.pk]))
        self.assertEqual(res_toggle.status_code, 302)
        habit.refresh_from_db()
        self.assertEqual(habit.streak_count, 1)
        self.assertTrue(habit.is_completed_today())
        self.assertEqual(
            HabitLog.objects.filter(habit=habit, date=timezone.localdate()).count(),
            1,
        )

        # Toggle again today -> untoggle
        self.client.post(reverse("habit_toggle", args=[habit.pk]))
        habit.refresh_from_db()
        self.assertEqual(habit.streak_count, 0)
        self.assertFalse(habit.is_completed_today())

        # Delete habit
        self.client.post(reverse("habit_delete", args=[habit.pk]))
        self.assertEqual(Habit.objects.filter(pk=habit.pk).count(), 0)

    def test_timeline_and_habits_views_load(self):
        res_timeline = self.client.get(reverse("todo_list") + "?view=timeline")
        self.assertEqual(res_timeline.status_code, 200)
        self.assertContains(res_timeline, "Timeline Gantt")

        res_habits = self.client.get(reverse("todo_list") + "?view=habits")
        self.assertEqual(res_habits.status_code, 200)
        self.assertContains(res_habits, "Habits &amp; Streaks")

    def test_wiki_page_crud(self):
        # Create wiki page
        self.client.post(
            reverse("wiki_add"),
            {
                "title": "Architettura Software",
                "category": "Ingegneria",
                "tags": "python, django, backend",
                "content": "Linee guida per la progettazione del codice.",
            },
        )
        page = WikiPage.objects.filter(title="Architettura Software").first()
        self.assertIsNotNone(page)
        self.assertEqual(page.category, "Ingegneria")
        self.assertIn("django", page.tag_list())

        # Edit wiki page
        self.client.post(
            reverse("wiki_edit", args=[page.pk]),
            {
                "title": "Architettura Software V2",
                "category": "Ingegneria",
                "tags": "python, django, microservices",
                "content": "Nuove note aggiornate.",
            },
        )
        page.refresh_from_db()
        self.assertEqual(page.title, "Architettura Software V2")

        # Delete wiki page
        self.client.post(reverse("wiki_delete", args=[page.pk]))
        self.assertEqual(WikiPage.objects.filter(pk=page.pk).count(), 0)

    def test_finance_and_savings_crud(self):
        # Add transaction
        self.client.post(
            reverse("transaction_add"),
            {
                "title": "Spesa Settimanale",
                "amount": "65.50",
                "transaction_type": "expense",
                "category": "Cibo",
                "notes": "Frutta e verdura",
            },
        )
        tx = Transaction.objects.filter(title="Spesa Settimanale").first()
        self.assertIsNotNone(tx)
        self.assertEqual(float(tx.amount), 65.50)

        # Add savings goal
        self.client.post(
            reverse("savings_add"),
            {
                "title": "Fondo Emergenze",
                "target_amount": "500",
                "current_amount": "100",
                "icon": "🛡️",
            },
        )
        goal = SavingsGoal.objects.filter(title="Fondo Emergenze").first()
        self.assertIsNotNone(goal)
        self.assertEqual(goal.percent_complete, 20)

        # Contribute to savings goal
        self.client.post(
            reverse("savings_contribute", args=[goal.pk]),
            {"amount": "50"},
        )
        goal.refresh_from_db()
        self.assertEqual(float(goal.current_amount), 150.0)
        self.assertEqual(goal.percent_complete, 30)

        # Delete
        self.client.post(reverse("transaction_delete", args=[tx.pk]))
        self.client.post(reverse("savings_delete", args=[goal.pk]))
        self.assertEqual(Transaction.objects.filter(pk=tx.pk).count(), 0)
        self.assertEqual(SavingsGoal.objects.filter(pk=goal.pk).count(), 0)

    def test_journal_entry_create_and_delete(self):
        today_str = timezone.localdate().strftime("%Y-%m-%d")
        self.client.post(
            reverse("journal_add"),
            {
                "date": today_str,
                "mood": "energetic",
                "weather": "☀️",
                "gratitude_1": "Il sole al mattino",
                "content": "Oggi grande sessione di produttività!",
            },
        )
        entry = JournalEntry.objects.filter(date=timezone.localdate()).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.mood, "energetic")
        self.assertEqual(entry.mood_emoji, "⚡")

        # Update entry for same day
        self.client.post(
            reverse("journal_add"),
            {
                "date": today_str,
                "mood": "calm",
                "weather": "⛅",
                "gratitude_1": "Una tisana calda",
                "content": "Serata di relax.",
            },
        )
        entry.refresh_from_db()
        self.assertEqual(entry.mood, "calm")
        self.assertEqual(entry.mood_emoji, "🧘")

        # Delete entry
        self.client.post(reverse("journal_delete", args=[entry.pk]))
        self.assertEqual(JournalEntry.objects.filter(pk=entry.pk).count(), 0)

    def test_media_item_crud_and_status(self):
        self.client.post(
            reverse("media_add"),
            {
                "title": "Atomic Habits",
                "creator": "James Clear",
                "media_type": "book",
                "status": "progress",
                "rating": "5",
                "review": "Lettura trasformativa",
            },
        )
        item = MediaItem.objects.filter(title="Atomic Habits").first()
        self.assertIsNotNone(item)
        self.assertEqual(item.status, "progress")

        # Mark as completed
        self.client.post(
            reverse("media_status_update", args=[item.pk]),
            {"status": "completed", "rating": "5"},
        )
        item.refresh_from_db()
        self.assertEqual(item.status, "completed")
        self.assertIsNotNone(item.completed_at)
        self.assertEqual(item.stars_display, "★★★★★")

        # Delete
        self.client.post(reverse("media_delete", args=[item.pk]))
        self.assertEqual(MediaItem.objects.filter(pk=item.pk).count(), 0)

    def test_rpg_rewards_and_xp(self):
        profile = UserProfileRPG.objects.create(coins=50, xp=150)
        self.assertEqual(profile.level, 2)

        # Add reward
        self.client.post(
            reverse("rpg_reward_add"),
            {
                "title": "Serata Pizzeria",
                "cost_coins": "30",
                "icon": "🍕",
            },
        )
        reward = RpgReward.objects.filter(title="Serata Pizzeria").first()
        self.assertIsNotNone(reward)
        self.assertFalse(reward.is_redeemed)

        # Redeem reward
        self.client.post(reverse("rpg_reward_redeem", args=[reward.pk]))
        reward.refresh_from_db()
        self.assertTrue(reward.is_redeemed)

        # Delete reward
        self.client.post(reverse("rpg_reward_delete", args=[reward.pk]))
        self.assertEqual(RpgReward.objects.filter(pk=reward.pk).count(), 0)

    def test_standalone_suites_views_load(self):
        views_to_test = [
            ("?view=wiki", "Second Brain"),
            ("?view=finance", "Finance"),
            ("?view=journal", "Journal"),
            ("?view=media", "Bookshelf"),
            ("?view=rpg", "Productivity RPG"),
            ("?view=soundscapes", "Soundscapes"),
            ("?view=ai_solver", "AI Problem Solver"),
        ]
        for query_param, expected_text in views_to_test:
            res = self.client.get(reverse("todo_list") + query_param)
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, expected_text)

    def test_api_ai_solve(self):
        # Valid problem request
        res = self.client.post(
            reverse("api_ai_solve"),
            data=json.dumps({"problem": "Continuo a procrastinare sullo studio"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("diagnosis", data)
        self.assertGreaterEqual(len(data["strategies"]), 1)
        self.assertGreaterEqual(len(data["tasks"]), 1)

        # Empty problem should return 400
        res_empty = self.client.post(
            reverse("api_ai_solve"),
            data=json.dumps({"problem": ""}),
            content_type="application/json",
        )
        self.assertEqual(res_empty.status_code, 400)

    def test_finance_export_csv(self):
        Transaction.objects.create(
            title="Cena Ristorante Test",
            amount=35.50,
            transaction_type="expense",
            category="food",
        )
        res = self.client.get(reverse("finance_export_csv"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=", res["Content-Disposition"])
        self.assertIn("Cena Ristorante Test", res.content.decode("utf-8"))

    def test_auth_pages_render(self):
        login_res = self.client.get(reverse("login"))
        self.assertEqual(login_res.status_code, 200)
        self.assertTemplateUsed(login_res, "registration/login.html")

        signup_res = self.client.get(reverse("signup"))
        self.assertEqual(signup_res.status_code, 200)
        self.assertTemplateUsed(signup_res, "registration/signup.html")
