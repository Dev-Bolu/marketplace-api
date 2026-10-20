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
    
    path("seller-profiles/", views.SellerProfileListView.as_view(),
    name="seller-profile-list"),
    path("seller-profiles/<int:pk>/", views.SellerProfileDetailView.as_view(),
    name="seller-profile-detail"),
    path("seller-profiles/me/",views.MySellerProfileView.as_view(),
    name="my-seller-profile"),
    
    
    path("stores/", views.StoreListView.as_view(), 
    name="store-list"),
    path("stores/<int:pk>/", views.StoreDetailView.as_view(),
    name="store-detail"),
    path("stores/me/", views.MyStoresView.as_view(),
    name="my-stores"),
    path("stores/me/<int:pk>/", views.MyStoresDetailView.as_view(),
    name="my-stores-detail"),
    
    path("token/",TokenObtainPairView.as_view(),
    name="token-obtain-pair"),
    path("token/refresh/",TokenRefreshView.as_view(),
    name="token-refresh"),
    
    path("register/", views.UserRegistrationView.as_view(), 
    name="user-register"),
    
    path("products/", views.ProductListView.as_view(), 
    name="product-list"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), 
    name="product-detail"),
    path("products/me/", views.MyProductListView.as_view(),
    name="my-product-list",),
    path("products/me/<int:pk>/", views.MyProductDetailView.as_view(),
    name="my-product-detail",),
    
    path("cart/", views.CartView.as_view(),
    name="cart",),
    path("cart/items/", views.CartItemView.as_view(),
    name="cart-item",),
    path("cart/items/",views.CartItemView.as_view(),
    name="cart-item-add"),
    path("cart/items/<int:pk>/", views.CartItemDetailView.as_view(),
    name="cart-item-detail"),

    
    ]