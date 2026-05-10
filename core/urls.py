from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # --- CORE & CONTENT ---
    path('', views.home_view, name='home'),
    path('content/', views.content_catalog, name='content_catalog'),
    path('content/<int:article_id>/', views.article_detail, name='article_detail'),
    path('thank-you/', views.thank_you_view, name='thank_you'),

    # --- THE ARSENAL & ENGINE ---
    path('tools/', views.tools_dashboard, name='tools'),
    path('arsenal/', views.my_arsenal, name='my_arsenal'),
    path('arsenal/settings/', views.arsenal_settings, name='arsenal_settings'),
    path('arsenal/engine/', views.discipline_engine, name='discipline_engine'),
    path('arsenal/leaderboard/', views.leaderboard, name='leaderboard'),
    path('arsenal/missions/', views.mission_map_detail, name='mission_map'),

    # --- AUTHENTICATION ---
    path('enlist/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('verify-email/', views.verify_email, name='verify_email'),

    # --- PASSWORD RESET ---
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="password_reset.html"), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset_sent.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), name="password_reset_complete"),

    # --- TOOL ACTIONS ---
    path('tools/add-habit/', views.add_habit, name='add_habit'),
    path('tools/log-habit/<int:habit_id>/', views.log_habit, name='log_habit'),
    path('tools/delete-habit/<int:habit_id>/', views.delete_habit, name='delete_habit'),
    path('tools/add-mission/', views.add_mission, name='add_mission'),
    path('tools/complete-mission/<int:mission_id>/', views.complete_mission, name='complete_mission'),
    path('tools/delete-mission/<int:mission_id>/', views.delete_mission, name='delete_mission'),

    # --- HEADQUARTERS OVERVIEW ---
    path('headquarters/', views.founder_dashboard, name='founder_dashboard'),
    path('headquarters/quick-drop/', views.quick_drop_upload, name='quick_drop_upload'),
    path('command-center/tools/', views.command_center_tools, name='command_center_tools'),

    # --- HQ: CONTENT MANAGER ---
    path('headquarters/content/', views.content_manager, name='content_manager'),
    path('headquarters/content/create/', views.content_create, name='content_create'),
    path('headquarters/content/edit/<int:article_id>/', views.content_edit, name='content_edit'),
    path('headquarters/content/delete/<int:article_id>/', views.content_delete, name='content_delete'),

    # --- HQ: USER MANAGER ---
    path('headquarters/users/', views.user_manager, name='user_manager'),
    path('headquarters/users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('headquarters/users/toggle-premium/<int:user_id>/', views.user_toggle_premium, name='user_toggle_premium'),

    # --- HQ: SUBSCRIBER MANAGER ---
    path('headquarters/subscribers/', views.subscriber_manager, name='subscriber_manager'),
    path('headquarters/subscribers/delete/<int:subscriber_id>/', views.subscriber_delete, name='subscriber_delete'),
]