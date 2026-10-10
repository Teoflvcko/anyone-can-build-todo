import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Todo

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
