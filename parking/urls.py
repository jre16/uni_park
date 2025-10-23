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
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vehicle/add/', views.add_vehicle, name='add_vehicle'),
    path('vehicle/edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicle/delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('search/', views.search_parking, name='search_parking'),
    path('parking-lot/<int:parking_lot_id>/', views.parking_lot_detail, name='parking_lot_detail'),
    path('api/nearby-parking/', views.get_nearby_parking, name='get_nearby_parking'),
    path('reserve/<int:parking_lot_id>/', views.reserve_parking, name='reserve_parking'),
]