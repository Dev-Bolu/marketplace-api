from django.urls import path
from . import views
urlpatterns = [
    path("welcome/", views.WelcomeView.as_view(), name="welcome"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    
]