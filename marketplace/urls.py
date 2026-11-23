from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns = [
    # Welcome & Auth
    path("welcome/", views.WelcomeView.as_view(), name="welcome"),
    path("register/", views.UserRegistrationView.as_view(), name="user-register"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/<int:pk>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("categories/me/", views.MyCategoriesView.as_view(), name="my-categories"),

    # Seller Profiles
    path("seller-profiles/", views.SellerProfileListView.as_view(), name="seller-profile-list"),
    path("seller-profiles/<int:pk>/", views.SellerProfileDetailView.as_view(), name="seller-profile-detail"),
    path("seller-profiles/me/", views.MySellerProfileView.as_view(), name="my-seller-profile"),

    # Stores
    path("stores/", views.StoreListView.as_view(), name="store-list"),
    path("stores/<int:pk>/", views.StoreDetailView.as_view(), name="store-detail"),
    path("stores/me/", views.MyStoresView.as_view(), name="my-stores"),
    path("stores/me/<int:pk>/", views.MyStoresDetailView.as_view(), name="my-stores-detail"),

    # Products
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("products/me/", views.MyProductListView.as_view(), name="my-product-list"),
    path("products/me/<int:pk>/", views.MyProductDetailView.as_view(), name="my-product-detail"),

    # Cart
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/items/", views.CartItemView.as_view(), name="cart-item"),
    path("cart/items/<int:pk>/", views.CartItemDetailView.as_view(), name="cart-item-detail"),

    # Buyer Orders & Checkout
    path("orders/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),

    # Vendor Dashboard Orders
    path("seller/orders/", views.SellerOrderListView.as_view(), name="seller-order-list"),
    path("seller/orders/<int:pk>/", views.SellerOrderDetailView.as_view(), name="seller-order-detail"),
]