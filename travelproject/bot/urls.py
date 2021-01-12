from django.urls import path
from bot import views

# 用來串接callback主程式
urlpatterns = [
    path('callback/', views.callback),
]