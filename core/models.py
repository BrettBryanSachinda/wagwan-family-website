from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

# --- 1. USER PROFILE ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    is_premium_member = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal: Auto-create Profile and Streak when a User registers
@receiver(post_save, sender=User)
def create_user_profile_and_streak(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        UserStreak.objects.get_or_create(user=instance)

# --- 2. CONTENT HUB ---
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Article(models.Model):
    CONTENT_TYPES = (('article', 'Article'), ('video', 'Video Transmission'))
    STATUS_CHOICES = (('draft', 'Draft'), ('published', 'Published'))
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    content_type = models.CharField(max_length=255, choices=CONTENT_TYPES, default='article')
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='draft')
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube/Vimeo embed link")
    content = models.TextField(blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:255]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

# --- 3. SUBSCRIBERS ---
class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

# --- 4. DISCIPLINE TRACKERS ---
class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    last_check_in = models.DateField(null=True, blank=True)

    def update_streak(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        if self.last_check_in == yesterday:
            self.current_streak += 1
        elif self.last_check_in == today:
            pass  # Already checked in today
        else:
            self.current_streak = 1
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        self.last_check_in = today
        self.save()

    def check_and_reset_streak(self):
        """Resets streak to 0 if a full day is missed."""
        if self.last_check_in:
            today = timezone.now().date()
            if today - self.last_check_in > timedelta(days=1):
                self.current_streak = 0
                self.save()

    @property
    def rank_title(self):
        if self.current_streak >= 90: return "Emperor"
        if self.current_streak >= 30: return "Commander"
        if self.current_streak >= 7:  return "Warrior"
        return "Initiate"

    @property
    def rank_color(self):
        if self.current_streak >= 90: return "#FF4500"
        if self.current_streak >= 30: return "#FFFFFF"
        if self.current_streak >= 7:  return "#A3A3A3"
        return "#404040"

    def __str__(self):
        return f"{self.user.username}: {self.current_streak} Days"

class DisciplineEngine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_completed_today(self):
        return self.logs.filter(date_completed=timezone.now().date()).exists()

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class DisciplineLog(models.Model):
    habit = models.ForeignKey(DisciplineEngine, on_delete=models.CASCADE, related_name='logs')
    date_completed = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ['habit', 'date_completed']

class MissionMap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='missions')
    title = models.CharField(max_length=255)
    deadline = models.DateField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Mission: {self.title}"