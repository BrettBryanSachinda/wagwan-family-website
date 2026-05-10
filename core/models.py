from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

# 1. USER PROFILE (Objective 2: Owned Audience)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    is_premium_member = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# 2. CONTENT HUB (Objective 1 & 5)
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
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    video_url = models.URLField(blank=True,null=True, help_text="YouTube/Vimeo link")
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='article')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_premium = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

# 3. DISCIPLINE ENGINE (Objective 4: Real Value)
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
            pass # Already updated today
        else:
            self.current_streak = 1
        
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
            
        self.last_check_in = today
        self.save()

    @property
    def rank_title(self):
        if self.current_streak >= 90: return "Emperor"
        if self.current_streak >= 30: return "Commander"
        if self.current_streak >= 7:  return "Warrior"
        return "Initiate"

    @property
    def rank_color(self):
        if self.current_streak >= 90: return "#FF4500" # Iconic Orange
        if self.current_streak >= 30: return "#FFFFFF" # Pure White
        if self.current_streak >= 7:  return "#A3A3A3" # Silver/Grey
        return "#404040" # Dim Grey

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
        return self.title

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email