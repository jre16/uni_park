from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, StudentSubscription
from .forms import SubscriptionForm

@login_required
def subscription_plans(request):
    """Display available subscription plans"""
    active_plans = SubscriptionPlan.objects.filter(is_active=True)
    current_subscription = StudentSubscription.objects.filter(
        student=request.user.studentprofile,
        status__in=['active', 'grace_period'],
        end_date__gt=timezone.now()
    ).first()
    
    context = {
        'plans': active_plans,
        'current_subscription': current_subscription
    }
    return render(request, 'parking/subscription/plans.html', context)

@login_required
def subscribe(request, plan_id):
    """Subscribe to a plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.student = request.user.studentprofile
            subscription.plan = plan
            subscription.start_date = timezone.now()
            subscription.end_date = subscription.start_date + timedelta(days=30)  # 30-day subscription
            
            # Cancel any active subscriptions
            StudentSubscription.objects.filter(
                student=request.user.studentprofile,
                status__in=['active', 'grace_period']
            ).update(
                status='cancelled',
                cancelled_at=timezone.now(),
                auto_renew=False
            )
            
            subscription.save()
            messages.success(request, f'Successfully subscribed to {plan.name}!')
            return redirect('parking:subscription_details', subscription_id=subscription.id)
    else:
        form = SubscriptionForm(initial={'plan': plan})
    
    return render(request, 'parking/subscription/subscribe.html', {
        'form': form,
        'plan': plan
    })

@login_required
def subscription_details(request, subscription_id):
    """View subscription details"""
    subscription = get_object_or_404(
        StudentSubscription,
        id=subscription_id,
        student=request.user.studentprofile
    )
    return render(request, 'parking/subscription/details.html', {
        'subscription': subscription
    })

@login_required
def cancel_subscription(request, subscription_id):
    """Cancel a subscription"""
    subscription = get_object_or_404(
        StudentSubscription,
        id=subscription_id,
        student=request.user.studentprofile,
        status__in=['active', 'grace_period']
    )
    
    if request.method == 'POST':
        subscription.cancel()
        messages.success(request, 'Your subscription has been cancelled.')
        return redirect('parking:subscription_plans')
    
    return render(request, 'parking/subscription/cancel.html', {
        'subscription': subscription
    })

@login_required
def subscription_history(request):
    """View subscription history"""
    subscriptions = StudentSubscription.objects.filter(
        student=request.user.studentprofile
    ).order_by('-created_at')
    
    return render(request, 'parking/subscription/history.html', {
        'subscriptions': subscriptions
    })