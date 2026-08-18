from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("seller-application/", views.seller_application, name="seller_application"),
    path("notifications/", views.notifications, name="notifications"),
]
