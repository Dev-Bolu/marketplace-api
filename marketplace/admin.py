from django.contrib import admin
from .models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
    SellerOrder,
    SellerProfile,
    Store,
)


# ==========================================
# INLINES (Nested Views Inside Parent Forms)
# ==========================================

class StoreInline(admin.TabularInline):
    model = Store
    extra = 0
    fields = ("store_name", "location", "is_active", "created_at")
    readonly_fields = ("created_at",)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "quantity", "subtotal")
    readonly_fields = ("subtotal",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "product_name", "seller_order", "quantity", "unit_price", "subtotal")
    readonly_fields = ("subtotal",)


class SellerOrderInline(admin.TabularInline):
    model = SellerOrder
    extra = 0
    fields = ("seller", "status", "total_amount", "created_at")
    readonly_fields = ("total_amount", "created_at")


# ==========================================
# MODEL ADMINS
# ==========================================

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "business_name", "user", "phone_number", "created_at")
    search_fields = ("business_name", "user__username", "user__email", "phone_number")
    readonly_fields = ("created_at", "updated_at")
    inlines = [StoreInline]


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id", "store_name", "seller", "location", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("store_name", "seller__business_name", "location")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "store", "category", "price", "stock", "is_active", "created_at")
    list_filter = ("is_active", "category", "store")
    search_fields = ("name", "description", "store__store_name")
    list_editable = ("price", "stock", "is_active")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    # Removed non-existent created_at/updated_at fields
    list_display = ("id", "user", "total_price")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("total_price",)
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "subtotal", "created_at")
    search_fields = ("cart__user__username", "product__name")
    readonly_fields = ("subtotal", "created_at", "updated_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email", "shipping_address")
    readonly_fields = ("total_amount", "created_at", "updated_at")
    inlines = [SellerOrderInline, OrderItemInline]


@admin.register(SellerOrder)
class SellerOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "seller", "status", "total_amount", "created_at")
    list_filter = ("status", "seller", "created_at")
    search_fields = ("id", "order__id", "seller__business_name", "order__user__username")
    readonly_fields = ("total_amount", "created_at", "updated_at")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    # Added product_name to list_display & search_fields
    list_display = ("id", "order", "seller_order", "product", "product_name", "quantity", "unit_price", "subtotal")
    search_fields = ("order__id", "product_name", "product__name", "seller_order__seller__business_name")
    readonly_fields = ("subtotal", "created_at", "updated_at")