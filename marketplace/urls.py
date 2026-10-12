from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("welcome/", views.WelcomeView.as_view(), name="welcome"),
    
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    
    path("categories/<int:pk>/", views.CategoryDetailView.as_view(),
    name="category-detail"),
    
    path("products/", views.ProductListView.as_view(), name="product-list"),

    path("products/<int:pk>/", views.ProductDetailView.as_view(),
    name="product-detail"),
    
    path("seller-profiles/", views.SellerProfileListView.as_view(), name="seller-profile-list"),
    
    path("token/",TokenObtainPairView.as_view(),
    name="token-obtain-pair"),

    path(
    "token/refresh/",TokenRefreshView.as_view(),
    name="token-refresh"),
    
    path("register/", views.UserRegistrationView.as_view(), name="user-register")
    ]