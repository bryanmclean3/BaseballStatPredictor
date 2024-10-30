"""
URL configuration for BaseballStatPredictor_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from BaseballStatPredictor import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', views.player_search, name='player_search'),
    path('player_stat_mode/', views.player_stat_mode, name='player_stat_mode'),
    path('head_to_head_mode/', views.head_to_head_mode, name='head_to_head_mode'),
    path('player_stat_mode_search/', views.player_stat_mode_search, name='player_stat_mode_search'),
    path('manual_stat_prediction_mode/', views.manual_stat_prediction_mode, name='manual_stat_prediction_mode'),
    path('get_player_prediction/', views.get_player_prediction, name='get_player_prediction'),
    path('batting_stat_prediction/', views.batting_stat_prediction, name='batting_stat_prediction'),
    path('pitching_stat_prediction/', views.pitching_stat_prediction, name='pitching_stat_prediction'),
    path('head_to_head_predictions/', views.head_to_head_predictions, name='head_to_head_predictions'),
    path('player_stat_predictions/', views.player_stat_predictions, name='player_stat_predictions'),
    path('previous_predictions/', views.previous_predictions, name='previous_predictions'),
    path('view_predictions/', views.view_predictions, name='view_predictions'),
    path("", views.search, name="search"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("callback/", views.callback, name="callback"),
]
