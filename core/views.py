from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Article, Subscriber, Category, UserProfile, UserStreak, DisciplineEngine, DisciplineLog, MissionMap
from .forms import WagwanRegistrationForm


# ================================================================
# PUBLIC PAGES
# ================================================================

def home_view(request):
    latest_articles = Article.objects.filter(status='published').order_by('-created_at')[:3]
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            if Subscriber.objects.filter(email=email).exists():
                messages.info(request, "You are already part of the family.")
            else:
                Subscriber.objects.create(email=email)
                return redirect('thank_you')
    return render(request, 'home.html', {'latest_articles': latest_articles})

def content_catalog(request):
    contents = Article.objects.filter(status='published').order_by('-created_at')
    return render(request, 'content_catalog.html', {'contents': contents})

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    # Increment view count
    Article.objects.filter(id=article_id).update(views_count=article.views_count + 1)
    return render(request, 'article_detail.html', {'article': article})

def thank_you_view(request):
    return render(request, 'thank_you.html')


# ================================================================
# AUTH
# ================================================================

def register_page(request):
    if request.user.is_authenticated:
        return redirect('my_arsenal')
    if request.method == 'POST':
        form = WagwanRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            UserStreak.objects.get_or_create(user=user)
            # Auto-subscribe their email
            email = form.cleaned_data.get('email')
            if email:
                Subscriber.objects.get_or_create(email=email)
            login(request, user)
            messages.success(request, "Welcome to the Family. Your arsenal awaits.")
            return redirect('my_arsenal')
    else:
        form = WagwanRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_page(request):
    from django.contrib.auth.forms import AuthenticationForm
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('my_arsenal')
    else:
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('home')

def verify_email(request):
    return render(request, 'verify_email.html')


# ================================================================
# THE ARSENAL
# ================================================================

@login_required
def my_arsenal(request):
    streak, _ = UserStreak.objects.get_or_create(user=request.user)
    habits = DisciplineEngine.objects.filter(user=request.user, is_active=True)
    missions = MissionMap.objects.filter(user=request.user, is_completed=False)
    for habit in habits:
        habit.done = habit.logs.filter(date_completed=timezone.now().date()).exists()
    return render(request, 'arsenal_dashboard.html', {
        'streak': streak,
        'habits': habits,
        'missions': missions,
    })

@login_required
def discipline_engine(request):
    habits = DisciplineEngine.objects.filter(user=request.user, is_active=True)
    return render(request, 'discipline_engine.html', {'habits': habits})

@login_required
def arsenal_settings(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_account':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been permanently deleted.')
            return redirect('home')

        # Default: update profile
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        if username:
            request.user.username = username
        if email:
            request.user.email = email
        request.user.save()
        messages.success(request, 'Settings updated.')
        return redirect('my_arsenal')

    return render(request, 'arsenal_settings.html')

@login_required
def tools_dashboard(request):
    streak, _ = UserStreak.objects.get_or_create(user=request.user)
    habits = DisciplineEngine.objects.filter(user=request.user, is_active=True)
    active_missions = MissionMap.objects.filter(user=request.user, is_completed=False).order_by('deadline')
    today = timezone.now().date()
    completed_today_count = sum(1 for h in habits if h.logs.filter(date_completed=today).exists())
    completed_missions_count = MissionMap.objects.filter(user=request.user, is_completed=True).count()
    return render(request, 'tools.html', {
        'streak': streak,
        'habits': habits,
        'active_missions': active_missions,
        'total_habits': habits.count(),
        'completed_today_count': completed_today_count,
        'completed_missions_count': completed_missions_count,
    })


# ================================================================
# ENGINE ACTIONS
# ================================================================

@login_required
def log_habit(request, habit_id):
    if request.method == 'POST':
        habit = get_object_or_404(DisciplineEngine, id=habit_id, user=request.user)
        log, created = DisciplineLog.objects.get_or_create(
            habit=habit,
            date_completed=timezone.now().date()
        )
        if not created:
            log.delete()
            return JsonResponse({'status': 'removed'})
        streak, _ = UserStreak.objects.get_or_create(user=request.user)
        streak.update_streak()
        return JsonResponse({'status': 'success', 'current_streak': streak.current_streak})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_habit(request):
    if request.method == 'POST':
        name = request.POST.get('habit_name')
        if name:
            DisciplineEngine.objects.create(user=request.user, name=name)
    return redirect('discipline_engine')

@login_required
def delete_habit(request, habit_id):
    habit = get_object_or_404(DisciplineEngine, id=habit_id, user=request.user)
    habit.is_active = False
    habit.save()
    return redirect('discipline_engine')

@login_required
def add_mission(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        deadline = request.POST.get('deadline')
        if title and deadline:
            MissionMap.objects.create(user=request.user, title=title, deadline=deadline)
    return redirect('my_arsenal')

@login_required
def complete_mission(request, mission_id):
    if request.method == 'POST':
        mission = get_object_or_404(MissionMap, id=mission_id, user=request.user)
        mission.is_completed = True
        mission.save()
    return redirect('my_arsenal')

@login_required
def delete_mission(request, mission_id):
    mission = get_object_or_404(MissionMap, id=mission_id, user=request.user)
    if request.method == 'POST':
        mission.delete()
        messages.success(request, "Mission scrubbed from the map.")
    return redirect('mission_map')


# ================================================================
# LEADERBOARD & MISSION MAP
# ================================================================

@login_required
def leaderboard(request):
    rankings = UserStreak.objects.select_related('user').order_by('-current_streak', '-best_streak')[:10]
    context = {
        'rankings': rankings,
        'user_streak': UserStreak.objects.filter(user=request.user).first(),
    }
    return render(request, 'leaderboard.html', context)

@login_required
def mission_map_detail(request):
    active_missions = MissionMap.objects.filter(user=request.user, is_completed=False).order_by('deadline')
    completed_missions = MissionMap.objects.filter(user=request.user, is_completed=True).order_by('-deadline')
    return render(request, 'mission_map.html', {
        'active_missions': active_missions,
        'completed_missions': completed_missions,
    })


# ================================================================
# FOUNDER HEADQUARTERS
# ================================================================

@staff_member_required
def founder_dashboard(request):
    from django.contrib.auth.models import User
    seven_days_ago = timezone.now() - timedelta(days=7)
    total_users = UserProfile.objects.count()
    total_subscribers = Subscriber.objects.count()
    total_articles = Article.objects.filter(status='published').count()
    new_members_count = User.objects.filter(date_joined__gte=seven_days_ago).count()
    top_posts = Article.objects.filter(status='published').order_by('-views_count')[:5]
    top_streaks = UserStreak.objects.select_related('user').order_by('-current_streak')[:5]
    return render(request, 'founder_dashboard.html', {
        'total_users': total_users,
        'total_subscribers': total_subscribers,
        'total_articles': total_articles,
        'new_members_count': new_members_count,
        'top_posts': top_posts,
        'top_streaks': top_streaks,
    })

@staff_member_required
def quick_drop_upload(request):
    return redirect('founder_dashboard')

@staff_member_required
def command_center_tools(request):
    recent_logs = DisciplineLog.objects.select_related('habit__user').order_by('-date_completed')[:15]
    top_streaks = UserStreak.objects.select_related('user').order_by('-current_streak')[:5]
    total_active_habits = DisciplineEngine.objects.filter(is_active=True).count()
    total_active_missions = MissionMap.objects.filter(is_completed=False).count()
    return render(request, 'command_center_tools.html', {
        'recent_logs': recent_logs,
        'top_streaks': top_streaks,
        'total_active_habits': total_active_habits,
        'total_active_missions': total_active_missions,
    })


# ================================================================
# HQ: CONTENT MANAGER (Full CRUD — no Django admin needed)
# ================================================================

@staff_member_required
def content_manager(request):
    articles = Article.objects.select_related('category', 'author').order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'hq_content_manager.html', {
        'articles': articles,
        'categories': categories,
    })

@staff_member_required
def content_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content_body = request.POST.get('content', '').strip()
        category_id = request.POST.get('category')
        content_type = request.POST.get('content_type', 'article')
        status = request.POST.get('status', 'draft')
        video_url = request.POST.get('video_url', '').strip()
        is_premium = request.POST.get('is_premium') == 'on'
        cover_image = request.FILES.get('cover_image')
        if title:
            article = Article(
                title=title,
                content=content_body,
                author=request.user,
                content_type=content_type,
                status=status,
                video_url=video_url or None,
                is_premium=is_premium,
            )
            if category_id:
                try:
                    article.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    pass
            if cover_image:
                article.cover_image = cover_image
            article.save()
            messages.success(request, f'"{title}" created successfully.')
            return redirect('content_manager')
    return render(request, 'hq_content_create.html', {'categories': categories})

@staff_member_required
def content_edit(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        article.title = request.POST.get('title', article.title).strip()
        article.content = request.POST.get('content', article.content).strip()
        article.content_type = request.POST.get('content_type', article.content_type)
        article.status = request.POST.get('status', article.status)
        article.video_url = request.POST.get('video_url', '').strip() or None
        article.is_premium = request.POST.get('is_premium') == 'on'
        category_id = request.POST.get('category')
        article.category = Category.objects.get(id=category_id) if category_id else None
        if request.FILES.get('cover_image'):
            article.cover_image = request.FILES['cover_image']
        article.save()
        messages.success(request, f'"{article.title}" updated.')
        return redirect('content_manager')
    return render(request, 'hq_content_edit.html', {'article': article, 'categories': categories})

@staff_member_required
def content_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f'"{title}" deleted.')
    return redirect('content_manager')


# ================================================================
# HQ: USER MANAGER
# ================================================================

@staff_member_required
def user_manager(request):
    from django.contrib.auth.models import User
    users = User.objects.select_related('profile', 'streak').order_by('-date_joined')
    return render(request, 'hq_user_manager.html', {'users': users})

@staff_member_required
def user_delete(request, user_id):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('user_manager')
        username = user.username
        user.delete()
        messages.success(request, f'"{username}" removed.')
    return redirect('user_manager')

@staff_member_required
def user_toggle_premium(request, user_id):
    profile = get_object_or_404(UserProfile, user__id=user_id)
    if request.method == 'POST':
        profile.is_premium_member = not profile.is_premium_member
        profile.save()
        status = "granted" if profile.is_premium_member else "revoked"
        messages.success(request, f'Premium {status} for {profile.user.username}.')
    return redirect('user_manager')


# ================================================================
# HQ: SUBSCRIBER MANAGER
# ================================================================

@staff_member_required
def subscriber_manager(request):
    subscribers = Subscriber.objects.order_by('-subscribed_at')
    return render(request, 'hq_subscriber_manager.html', {'subscribers': subscribers})

@staff_member_required
def subscriber_delete(request, subscriber_id):
    sub = get_object_or_404(Subscriber, id=subscriber_id)
    if request.method == 'POST':
        sub.delete()
        messages.success(request, 'Subscriber removed.')
    return redirect('subscriber_manager')