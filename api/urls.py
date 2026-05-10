from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('findcar/', views.findcar, name='findcar'),
    path('comparecar/', views.comparecar, name='comparecar'),
    path('sellcar/', views.sellcar, name='sellcar'),
    path('vehicle/<int:vehicle_id>/', views.vehicle_details, name='vehicle_details'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # ✅ CRUD routes for vehicles
    path('add_vehicle/', views.add_vehicle, name='add_vehicle'),
    path('update_vehicle/<int:vehicle_id>/', views.update_vehicle, name='update_vehicle'),
    path('delete_vehicle/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('vehicle/<int:vehicle_id>/', views.vehicle_details, name='vehicle'),
]
