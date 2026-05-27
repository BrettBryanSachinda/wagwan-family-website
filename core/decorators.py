"""
Custom decorators for Wagwan Family views.
Provides proper permission checks with user-friendly redirects.
"""
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def staff_required(view_func):
    """
    Custom decorator for staff-only views.
    Redirects non-staff users to home with a message instead of Django admin.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'You need to be logged in to access this area.')
            return redirect('login')
        
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this area. Staff access only.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def superuser_required(view_func):
    """
    Custom decorator for superuser-only views.
    Redirects non-superuser users to home with a message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'You need to be logged in to access this area.')
            return redirect('login')
        
        if not request.user.is_superuser:
            messages.error(request, 'You do not have permission to access this area. Administrator access only.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
