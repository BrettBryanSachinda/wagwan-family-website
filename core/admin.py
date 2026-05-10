from django.contrib import admin
from .models import Article, Subscriber, Category, UserStreak, DisciplineEngine, DisciplineLog, MissionMap, UserProfile

# 1. User Profile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_premium_member')
    list_filter = ('is_premium_member',)
    search_fields = ('user__username', 'user__email')

# 2. Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)} # This auto-types the slug for Simba

# 3. Article Admin (The Content Hub)
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    # UPGRADE 1: Added 'views_count' to list_display so you can see views in the admin panel
    list_display = ('title', 'category', 'author', 'status', 'is_premium', 'views_count', 'created_at')
    list_filter = ('status', 'is_premium', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)} # Auto-types the slug based on the title
    date_hierarchy = 'created_at' # Adds a cool date timeline at the top

    # UPGRADE 2: Auto-assigns the logged-in admin as the author when creating a post
    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.author = request.user
        obj.save()

# 4. Subscriber Admin
@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)

# Optional: Customize the Admin Header Text
admin.site.site_header = "Wagwan Family Headquarters"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the Wagwan Empire"

# --- WAGWAN FAMILY TOOLS ADMIN ---

@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'best_streak', 'last_check_in')
    search_fields = ('user__username',)

@admin.register(DisciplineEngine)
class DisciplineEngineAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'name')

@admin.register(DisciplineLog)
class DisciplineLogAdmin(admin.ModelAdmin):
    list_display = ('habit', 'date_completed')
    list_filter = ('date_completed',)
    search_fields = ('habit__user__username', 'habit__name')

@admin.register(MissionMap)
class MissionMapAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'deadline', 'is_completed')
    list_filter = ('is_completed', 'deadline')
    search_fields = ('user__username', 'title')
