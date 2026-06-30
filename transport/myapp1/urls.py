from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('about', views.about),
    path('contact', views.contact),
    path('book', views.book),
    path('register', views.register),
    path('login', views.login),
    path('dashboard', views.dashboard),
    path('logout', views.logout),

    path('save', views.save),
    path('check', views.check),
    path('savebook', views.savebook),
    path('payment', views.payment),
    path('editprofile', views.editprofile),
    path('saveeditprofile', views.saveeditprofile),

    path('forget', views.forget),
    path('verify_otp', views.verify_otp),
    path('send_otp', views.send_otp),
    path('reset_password', views.reset_password),

    # AJAX: distance calculation
    path('calculate_distance', views.calculate_distance),

    # Delivery Tracking (Customer)
    path('track/<int:booking_id>/', views.track_delivery, name='track_delivery'),
    path('api/tracking/<int:booking_id>/', views.get_tracking_data, name='get_tracking_data'),
    path('api/update_location/<int:booking_id>/', views.update_driver_location, name='update_driver_location'),

    # Driver Live GPS Sharing (Driver opens on phone)
    path('driver/<int:booking_id>/<str:share_key>/', views.driver_tracking_page, name='driver_tracking_page'),
    path('driver/<int:booking_id>/<str:share_key>/gps/', views.driver_update_gps, name='driver_update_gps'),
]