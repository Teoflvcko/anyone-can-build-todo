from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="projects",
    )
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default="📁")
    color = models.CharField(max_length=20, default="#a855f7")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.icon} {self.name}"


class Todo(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    ]

    RECURRENCE_CHOICES = [
        ("none", "None"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    ENERGY_CHOICES = [
        ("low", "Low Energy ☕"),
        ("medium", "Medium ⚡"),
        ("high", "Deep Work 🧠"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="todos",
    )
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="shared_todos",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=50, blank=True, default="")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="todo",
    )
    recurrence = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        default="none",
    )
    energy_level = models.CharField(
        max_length=20,
        choices=ENERGY_CHOICES,
        default="medium",
    )
    tags = models.CharField(max_length=200, blank=True, default="")
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="todos",
    )
    due_date = models.DateField(null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(default=0, blank=True)
    actual_minutes = models.PositiveIntegerField(default=0, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip().lstrip("#") for t in self.tags.split(",") if t.strip()]

    @property
    def relative_deadline_display(self):
        if not self.due_date:
            return ""
        today = timezone.localdate()
        diff = (self.due_date - today).days
        if diff < 0:
            return f"Overdue by {abs(diff)}d"
        elif diff == 0:
            return "Today"
        elif diff == 1:
            return "Tomorrow"
        return f"In {diff}d"

    @property
    def is_overdue(self):
        if self.due_date and not self.done:
            return self.due_date < timezone.localdate()
        return False

    @property
    def is_due_today(self):
        if self.due_date and not self.done:
            return self.due_date == timezone.localdate()
        return False

    @property
    def is_due_tomorrow(self):
        if self.due_date and not self.done:
            return self.due_date == (timezone.localdate() + timedelta(days=1))
        return False

    @property
    def formatted_duration(self):
        """Format estimated minutes into human-readable duration."""
        if not self.estimated_minutes:
            return ""
        if self.estimated_minutes < 60:
            return f"{self.estimated_minutes}m"
        hours = self.estimated_minutes // 60
        mins = self.estimated_minutes % 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"

    @property
    def formatted_actual_duration(self):
        """Format actual tracked minutes into human-readable duration."""
        if not self.actual_minutes:
            return ""
        if self.actual_minutes < 60:
            return f"{self.actual_minutes}m"
        hours = self.actual_minutes // 60
        mins = self.actual_minutes % 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"

    @property
    def completed_subtasks_count(self):
        return self.subtasks.filter(done=True).count()

    @property
    def total_subtasks_count(self):
        return self.subtasks.count()

    @property
    def subtasks_progress_percent(self):
        total = self.total_subtasks_count
        if total == 0:
            return 100 if self.done else 0
        return int((self.completed_subtasks_count / total) * 100)


class SubTask(models.Model):
    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE,
        related_name="subtasks",
    )
    title = models.CharField(max_length=200)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title


class CollaborationEvent(models.Model):
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    event_date = models.DateField()
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="joined_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["event_date"]

    def __str__(self):
        return f"{self.title} ({self.event_date})"


class SocialActivity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.message}"


class TaskComment(models.Model):
    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.message}"


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="habits",
    )
    name = models.CharField(max_length=150)
    streak_count = models.PositiveIntegerField(default=0)
    last_completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-streak_count", "name"]

    def __str__(self):
        return f"{self.name} (🔥 {self.streak_count})"

    def is_completed_today(self):
        return self.last_completed_date == timezone.localdate()


class HabitLog(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    date = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["habit", "date"], name="unique_habit_log_per_day"
            )
        ]

    def __str__(self):
        return f"{self.habit.name} - {self.date}"


class WikiPage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="wiki_pages",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    category = models.CharField(max_length=50, default="Generale")
    tags = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("income", "Entrata"),
        ("expense", "Uscita"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transactions",
    )
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default="expense"
    )
    category = models.CharField(max_length=50, default="Altro")
    date = models.DateField(default=timezone.localdate)
    notes = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        prefix = "+" if self.transaction_type == "income" else "-"
        return f"{prefix}€{self.amount} - {self.title} ({self.category})"


class SavingsGoal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="savings_goals",
    )
    title = models.CharField(max_length=150)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    icon = models.CharField(max_length=20, default="🎯")
    target_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["target_date", "-created_at"]

    def __str__(self):
        return f"{self.icon} {self.title}: €{self.current_amount}/€{self.target_amount}"

    @property
    def percent_complete(self):
        if self.target_amount > 0:
            return min(100, int((self.current_amount / self.target_amount) * 100))
        return 0


class JournalEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="journal_entries",
    )
    date = models.DateField(default=timezone.localdate)
    mood = models.CharField(max_length=20, default="calm")
    weather = models.CharField(max_length=20, default="☀️")
    gratitude_1 = models.CharField(max_length=255, blank=True, default="")
    gratitude_2 = models.CharField(max_length=255, blank=True, default="")
    gratitude_3 = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"Diario del {self.date} ({self.mood})"

    @property
    def mood_emoji(self):
        emojis = {
            "radiant": "😄",
            "energetic": "⚡",
            "calm": "🧘",
            "tired": "😴",
            "stressed": "🤯",
        }
        return emojis.get(self.mood, "📝")


class MediaItem(models.Model):
    TYPE_CHOICES = [
        ("book", "Libro"),
        ("movie", "Film/Serie"),
        ("course", "Corso"),
        ("podcast", "Podcast"),
        ("game", "Videogioco"),
    ]
    STATUS_CHOICES = [
        ("want", "Da iniziare"),
        ("progress", "In corso"),
        ("completed", "Completato"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="media_items",
    )
    title = models.CharField(max_length=200)
    creator = models.CharField(max_length=150, blank=True, default="")
    media_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="book")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="want")
    rating = models.PositiveSmallIntegerField(default=5)
    review = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=10, default="📚")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.icon} {self.title} ({self.status})"

    @property
    def stars_display(self):
        return "★" * self.rating + "☆" * (5 - self.rating)


class UserProfileRPG(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rpg_profile",
    )
    xp = models.PositiveIntegerField(default=120)
    coins = models.PositiveIntegerField(default=50)
    discipline_stat = models.PositiveIntegerField(default=10)
    creativity_stat = models.PositiveIntegerField(default=10)
    focus_stat = models.PositiveIntegerField(default=10)
    vitality_stat = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profilo RPG"
        verbose_name_plural = "Profili RPG"

    def __str__(self):
        return f"Livello {self.level} - {self.rank_title}"

    @property
    def level(self):
        return 1 + (self.xp // 100)

    @property
    def xp_in_level(self):
        return self.xp % 100

    @property
    def rank_title(self):
        lvl = self.level
        if lvl >= 10:
            return "Signore del Tempo 👑"
        if lvl >= 7:
            return "Gran Maestro della Mente 🔮"
        if lvl >= 5:
            return "Stratega del Focus ⚔️"
        if lvl >= 3:
            return "Esploratore delle Idee 🧭"
        return "Novizio della Produttività 🌱"


class RpgReward(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rpg_rewards",
    )
    title = models.CharField(max_length=150)
    cost_coins = models.PositiveIntegerField(default=30)
    icon = models.CharField(max_length=20, default="🎁")
    is_redeemed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_redeemed", "cost_coins"]

    def __str__(self):
        status = " (Riscattato)" if self.is_redeemed else ""
        return f"{self.icon} {self.title} - {self.cost_coins} monete{status}"
