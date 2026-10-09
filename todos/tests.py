from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
            },
        )
        todo = Todo.objects.get()
        self.assertEqual(todo.title, "Buy groceries")
        self.assertEqual(todo.category, "Home")
        self.assertEqual(todo.priority, "high")
        self.assertEqual(str(todo.due_date), "2026-10-15")
        self.assertEqual(todo.description, "Apples, Milk, Bread")

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
        )
        self.client.post(reverse("todo_duplicate", args=[todo.pk]))
        self.assertEqual(Todo.objects.count(), 2)
        duplicated = Todo.objects.get(title="Design landing page (Copy)")
        self.assertEqual(duplicated.category, "Work")
        self.assertEqual(duplicated.priority, "high")
        self.assertFalse(duplicated.done)

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

    def test_api_todos_endpoint(self):
        Todo.objects.create(title="API task")
        res = self.client.get(reverse("api_todos"))
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(len(json_data["todos"]), 1)
        self.assertEqual(json_data["todos"][0]["title"], "API task")

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
