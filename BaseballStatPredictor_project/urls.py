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
from BaseballStatPredictor.views import player_search, get_player_prediction, player_stat_mode, player_stat_mode_search, best_player_stat_mode_search, head_to_head_mode, best_player_stat_mode

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', player_search, name='player_search'),
    path('player_stat_mode/', player_stat_mode, name='player_stat_mode'),
    path('head_to_head_mode/', head_to_head_mode, name='head_to_head_mode'),
    path('best_player_stat_mode/', best_player_stat_mode, name='best_player_stat_mode'),
    path('player_stat_mode_search/', player_stat_mode_search, name='player_stat_mode_search'),
    path('best_player_stat_mode_search/', best_player_stat_mode_search, name='best_player_stat_mode_search'),
    path('get_player_prediction/', get_player_prediction, name='get_player_prediction'),
]
