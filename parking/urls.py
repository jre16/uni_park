from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'parking'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('verify/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password/reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path(
        'password/reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'password/reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings_view, name='settings'),
    path('language-toggle/', views.toggle_language, name='toggle_language'),
    path('hero/location/', views.hero_location, name='hero_location'),
    path('vehicle/add/', views.add_vehicle, name='add_vehicle'),
    path('vehicle/edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicle/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('find/', views.find_parking, name='find_parking'),
    path('parking-lot/<int:parking_lot_id>/', views.parking_lot_detail, name='parking_lot_detail'),
    path('api/nearby-parking/', views.get_nearby_parking, name='get_nearby_parking'),
    path('home/reservation-card/', views.home_reservation_card, name='home_reservation_card'),
    path('reserve/<int:parking_lot_id>/', views.reserve_partial, name='reserve_partial'),
    path('cancel/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('checkin/<int:reservation_id>/', views.check_in, name='check_in'),

]