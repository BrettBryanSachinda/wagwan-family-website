from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import F
from django.utils import timezone
from django.utils.html import escape
from datetime import timedelta, datetime
import re
from .models import Article, Subscriber, Category, UserProfile, UserStreak, DisciplineEngine, DisciplineLog, MissionMap
from .forms import WagwanRegistrationForm, UserProfileForm
from .decorators import staff_required, superuser_required


# ================================================================
# PUBLIC PAGES
# ================================================================

def home_view(request):
    latest_articles = Article.objects.filter(status='published').order_by('-created_at')[:3]
    premium_articles = Article.objects.filter(status='published', is_premium=True).order_by('-created_at')[:3]
    
    # Fixed: Repaired indentation rules across form processing
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            try:
                subscriber, created = Subscriber.objects.get_or_create(email=email)
                if not created:
                    messages.info(request, "You are already part of the family.")
                else:
                    return redirect('thank_you')
            except IntegrityError:
                # Handles simultaneous submission clicks gracefully
                messages.info(request, "You are already part of the family.")
        
    return render(request, 'home.html', {
        'latest_articles': latest_articles,
        'premium_articles': premium_articles,
    })

def content_catalog(request):
    contents = Article.objects.filter(status='published').order_by('-created_at')
    return render(request, 'content_catalog.html', {'contents': contents})

def article_detail(request, article_id):
    """Display article with premium access control."""
    article = get_object_or_404(Article, id=article_id)
    
    # Check if user can access this content
    can_access = True
    if article.is_premium:
        # Premium articles: only accessible to authenticated premium members
        if not request.user.is_authenticated:
            can_access = False
        else:
            try:
                profile = request.user.profile
                can_access = profile.is_premium_member
            except:
                can_access = False
    
    # Increment view count (only for accessible content)
    if can_access:
        Article.objects.filter(id=article_id).update(views_count=F('views_count') + 1)
    
    return render(request, 'article_detail.html', {
        'article': article,
        'can_access': can_access
    })

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
            email = form.cleaned_data.get('email')
            if email:
                Subscriber.objects.get_or_create(email=email)
            login(request, user)
            messages.success(request, "Welcome to the Family. Complete your profile.")
            return redirect('profile_setup')  # Go to profile setup first
    else:
        form = WagwanRegistrationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def profile_setup(request):
    """Post-registration profile setup — upload photo and bio with validation."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Sanitize and save bio
            bio = escape(form.cleaned_data.get('bio', '').strip())
            profile.bio = bio
            
            # Save profile picture if provided
            if form.cleaned_data.get('profile_picture'):
                profile.profile_picture = form.cleaned_data['profile_picture']
            
            profile.save()
            messages.success(request, "Profile set. Welcome to the Arsenal.")
            return redirect('my_arsenal')
        else:
            # Form has errors, display them
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Pre-populate form with existing data
        form = UserProfileForm(initial={
            'bio': profile.bio if profile.bio else '',
        })
    
    # Allow skipping
    if request.GET.get('skip'):
        return redirect('my_arsenal')
    
    return render(request, 'profile_setup.html', {'profile': profile, 'form': form})

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
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    habits = DisciplineEngine.objects.filter(user=request.user, is_active=True)
    missions = MissionMap.objects.filter(user=request.user, is_completed=False)
    
    streak.check_and_reset_streak()

    # Optimized: Get all habit IDs completed today by this user in 1 query
    today = timezone.now().date()
    completed_today_ids = set(
        DisciplineLog.objects.filter(
            habit__user=request.user, 
            date_completed=today
        ).values_list('habit_id', flat=True)
    )

    # Fast in-memory check without hitting the database again
    for habit in habits:
        habit.done = habit.id in completed_today_ids
    
    return render(request, 'arsenal_dashboard.html', {
        'streak': streak,
        'profile': profile,
        'habits': habits,
        'missions': missions,
    })


@login_required
def discipline_engine(request):
    habits = DisciplineEngine.objects.filter(user=request.user, is_active=True)
    return render(request, 'discipline_engine.html', {'habits': habits})

@login_required
def arsenal_settings(request):
    """User settings: update profile or delete account with validation."""
    # 1. Fetch the user's profile right away so we can update it and send it to the template
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_account':
            # Require confirmation to prevent accidental deletion
            confirm = request.POST.get('confirm_delete')
            if confirm == 'yes':
                user = request.user
                username = user.username
                logout(request)
                user.delete()
                messages.success(request, f'Account "{username}" has been permanently deleted.')
                return redirect('home')
            else:
                messages.warning(request, 'Account deletion cancelled. Check the confirmation box to proceed.')
                return redirect('arsenal_settings')

        # Default: update profile with validation
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        
        # 2. ADDED: Grab the bio and the uploaded file!
        bio = request.POST.get('bio', '').strip()
        profile_picture = request.FILES.get('profile_picture')
        
        errors = []
        
        # Validate username
        if username:
            if len(username) < 3:
                errors.append('Username must be at least 3 characters.')
            elif len(username) > 30:
                errors.append('Username must be under 30 characters.')
            elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
                errors.append('Username can only contain letters, numbers, hyphens, and underscores.')
            elif username != request.user.username and User.objects.filter(username=username).exists():
                errors.append('This username is already taken.')
            else:
                request.user.username = username
        
        # Validate email
        if email:
            if '@' not in email or '.' not in email:
                errors.append('Invalid email format.')
            elif email != request.user.email and User.objects.filter(email=email).exists():
                errors.append('This email is already in use.')
            else:
                request.user.email = email
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('arsenal_settings')
        
        # 3. Save the base User model (Username & Email)
        request.user.save()
        
        # 4. ADDED: Save the UserProfile model (Bio & Profile Picture)
        profile.bio = bio
        if profile_picture:
            profile.profile_picture = profile_picture
        profile.save()

        messages.success(request, 'Settings updated successfully.')
        return redirect('my_arsenal')

    # 5. ADDED: Pass the profile to the template so the current bio and picture load properly
    return render(request, 'arsenal_settings.html', {'profile': profile})

@login_required
def tools_dashboard(request):
    streak, _ = UserStreak.objects.get_or_create(user=request.user)
    habits = DisciplineEngine.objects.filter(user=request.user, is_active=True)
    active_missions = MissionMap.objects.filter(user=request.user, is_completed=False).order_by('deadline')
    today = timezone.now().date()
    completed_today_count = sum(1 for h in habits if h.logs.filter(date_completed=today).exists())
    completed_missions_count = MissionMap.objects.filter(user=request.user, is_completed=True).count()

    # Optimized: Get all habit IDs completed today by this user in 1 query
    today = timezone.now().date()
    completed_today_ids = set(
        DisciplineLog.objects.filter(
            habit__user=request.user, 
            date_completed=today
        ).values_list('habit_id', flat=True)
    )

    # Fast in-memory check without hitting the database again
    for habit in habits:
        habit.done = habit.id in completed_today_ids

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
        try:
            habit = DisciplineEngine.objects.get(id=habit_id, user=request.user)
        except DisciplineEngine.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Habit not found.'}, status=404)
        today = timezone.now().date()
        
        # Check if already logged today
        log, created = DisciplineLog.objects.get_or_create(habit=habit, date_completed=today)
        
        streak, _ = UserStreak.objects.get_or_create(user=request.user)
        
        if created:
            # First time logging today
            if streak.last_check_in != today:
                streak.current_streak += 1
                if streak.current_streak > streak.best_streak:
                    streak.best_streak = streak.current_streak
                streak.last_check_in = today
                streak.save()
            status = 'success'
        else:
            # Un-checking the habit
            log.delete()
            # Note: We don't subtract streak points immediately to avoid punishing a misclick
            status = 'removed'
            
        return JsonResponse({'status': status, 'current_streak': streak.current_streak})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_habit(request):
    """Add a new habit with validation."""
    if request.method == 'POST':
        name = escape(request.POST.get('habit_name', '').strip())
        
        # Validate habit name
        if not name:
            messages.error(request, 'Habit name cannot be empty.')
        elif len(name) < 3:
            messages.error(request, 'Habit name must be at least 3 characters.')
        elif len(name) > 150:
            messages.error(request, 'Habit name must be under 150 characters.')
        else:
            # Check for duplicates
            if DisciplineEngine.objects.filter(user=request.user, name=name, is_active=True).exists():
                messages.warning(request, 'You already have a habit with this name.')
            else:
                DisciplineEngine.objects.create(user=request.user, name=name)
                messages.success(request, f'Habit "{name}" added to your arsenal.')
    
    return redirect('discipline_engine')

@login_required
def delete_habit(request, habit_id):
    habit = get_object_or_404(DisciplineEngine, id=habit_id, user=request.user)
    habit.is_active = False
    habit.save()
    return redirect('discipline_engine')

@login_required
def add_mission(request):
    """Add a new mission with validation."""
    if request.method == 'POST':
        title = escape(request.POST.get('title', '').strip())
        deadline = request.POST.get('deadline')
        
        # Validate mission title
        if not title:
            messages.error(request, 'Mission title cannot be empty.')
        elif len(title) < 3:
            messages.error(request, 'Mission title must be at least 3 characters.')
        elif len(title) > 255:
            messages.error(request, 'Mission title must be under 255 characters.')
        # Validate deadline
        elif not deadline:
            messages.error(request, 'Mission deadline is required.')
        else:
            try:
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                if deadline_date < timezone.now().date():
                    messages.error(request, 'Mission deadline must be in the future.')
                else:
                    MissionMap.objects.create(user=request.user, title=title, deadline=deadline_date)
                    messages.success(request, f'Mission "{title}" added to your map.')
            except ValueError:
                messages.error(request, 'Invalid deadline format.')
    
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
    # Determine the cutoff point (anything before yesterday means the streak is dead)
    cutoff_date = timezone.now().date() - timedelta(days=1)

    # Bulk reset everyone who missed their check-in window in a single query
    # Using __lt handles both DateField and DateTimeField safely across DB engines
    UserStreak.objects.filter(last_check_in__lt=cutoff_date).update(current_streak=0)

    # Fetch top 10 rankings efficiently
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

@staff_required
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

@staff_required
def quick_drop_upload(request):
    if request.method == 'POST' and request.FILES.get('media_file'):
        media_file = request.FILES['media_file']
        title = request.POST.get('title', '').strip()

        # If no title is typed, just use the file name
        if not title:
            title = media_file.name

        # Detect if it's a video or an image
        content_type = 'article'  # Default to article/picture
        if media_file.content_type.startswith('video/'):
            content_type = 'video'

        # Create the post and publish it immediately
        article = Article.objects.create(
            title=title,
            author=request.user,
            content_type=content_type,
            status='published',
            is_premium=False
        )

        # Attach the file to the correct database field
        if content_type == 'video':
            article.video_file = media_file
        else:
            article.cover_image = media_file

        article.save()
        messages.success(request, f'Quick Drop "{title}" deployed successfully!')
    else:
        messages.error(request, 'Action failed: No file detected.')

    return redirect('founder_dashboard')

@staff_required
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

@staff_required
def content_manager(request):
    articles = Article.objects.select_related('category', 'author').order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'hq_content_manager.html', {
        'articles': articles,
        'categories': categories,
    })

@staff_required
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
            return redirect('hq_content_manager')
    return render(request, 'hq_content_create.html', {'categories': categories})

@staff_required
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
        return redirect('hq_content_manager')
    return render(request, 'hq_content_edit.html', {'article': article, 'categories': categories})

@staff_required
def content_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f'"{title}" deleted.')
    return redirect('hq_content_manager')


# ================================================================
# HQ: USER MANAGER
# ================================================================

@staff_required
def user_manager(request):
    from django.contrib.auth.models import User
    users = User.objects.select_related('profile', 'streak').order_by('-date_joined')
    return render(request, 'hq_user_manager.html', {'users': users})

@staff_required
def user_delete(request, user_id):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('hq_user_manager')
        username = user.username
        user.delete()
        messages.success(request, f'"{username}" removed.')
    return redirect('hq_user_manager')

@staff_required
def user_toggle_premium(request, user_id):
    profile = get_object_or_404(UserProfile, user__id=user_id)
    if request.method == 'POST':
        profile.is_premium_member = not profile.is_premium_member
        profile.save()
        status = "granted" if profile.is_premium_member else "revoked"
        messages.success(request, f'Premium {status} for {profile.user.username}.')
    return redirect('hq_user_manager')


# ================================================================
# HQ: SUBSCRIBER MANAGER
# ================================================================

@staff_required
def subscriber_manager(request):
    subscribers = Subscriber.objects.order_by('-subscribed_at')
    return render(request, 'hq_subscriber_manager.html', {'subscribers': subscribers})

@staff_required
def subscriber_delete(request, subscriber_id):
    sub = get_object_or_404(Subscriber, id=subscriber_id)
    if request.method == 'POST':
        sub.delete()
        messages.success(request, 'Subscriber removed.')
    return redirect('hq_subscriber_manager')


# ================================================================
# USER PROFILES & PREMIUM
# ================================================================

def user_profile(request, username):
    """Display a user's public profile with stats and rank."""
    from django.contrib.auth.models import User
    
    profile_user = get_object_or_404(User, username=username)
    profile = UserProfile.objects.filter(user=profile_user).first()
    streak = UserStreak.objects.filter(user=profile_user).first()
    
    # Check if viewing own profile
    is_own_profile = request.user == profile_user
    
    # Get global rank position
    all_streaks = UserStreak.objects.select_related('user').order_by('-current_streak', '-best_streak')
    rank_position = None
    for idx, s in enumerate(all_streaks, 1):
        if s.user == profile_user:
            rank_position = idx
            break
    
    # Get mission and habit counts
    completed_missions = MissionMap.objects.filter(user=profile_user, is_completed=True).count()
    total_habits = DisciplineEngine.objects.filter(user=profile_user, is_active=True).count()
    
    # Reset streak if missed days
    if streak:
        streak.check_and_reset_streak()
    
    context = {
        'profile_user': profile_user,
        'profile': profile,
        'streak': streak,
        'is_own_profile': is_own_profile,
        'rank_position': rank_position,
        'completed_missions': completed_missions,
        'total_habits': total_habits,
    }
    
    return render(request, 'user_profile.html', context)


def premium_upgrade(request):
    """Display premium membership upgrade page."""
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        is_premium = profile.is_premium_member if profile else False
    else:
        is_premium = False
    
    context = {'is_premium': is_premium}
    return render(request, 'premium_upgrade.html', context)


@login_required
def premium_request(request):
    """Handle premium membership requests from users."""
    if request.method == 'POST':
        # In a real app, this would send an email or create a support ticket
        # For now, we'll just show a message
        messages.info(request, 'Thank you for your interest in Premium. We will contact you shortly.')
        return redirect('my_arsenal')
    
    return redirect('premium_upgrade')