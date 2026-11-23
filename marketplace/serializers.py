from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

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


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Handles new user registration with email uniqueness validation."""
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for managing product categories with case-insensitive name validation."""
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        value = value.strip()
        categories = Category.objects.filter(name__iexact=value)
        if self.instance:
            categories = categories.exclude(pk=self.instance.pk)
        if categories.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class SellerProfileSerializer(serializers.ModelSerializer):
    """Displays seller profile information."""
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = SellerProfile
        fields = [
            "id",
            "username",
            "business_name",
            "phone_number",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StoreSerializer(serializers.ModelSerializer):
    """Serializer for store management."""
    seller = serializers.CharField(source="seller.business_name", read_only=True)

    class Meta:
        model = Store
        fields = [
            "id",
            "seller",
            "store_name",
            "description",
            "location",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "seller", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for creating, updating, and displaying public products."""
    store_id = serializers.PrimaryKeyRelatedField(
        source="store",
        queryset=Store.objects.all(),
        write_only=True,
    )
    store = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "store",
            "store_id",
            "category",
            "name",
            "description",
            "price",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "store", "created_at", "updated_at"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Product name cannot be empty.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value


class CartProductSerializer(serializers.ModelSerializer):
    """Restricted product representation tailored for buyers in the cart context."""
    store_name = serializers.CharField(source="store.store_name", read_only=True)
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    in_stock = serializers.SerializerMethodField()
    low_stock_alert = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
            "store_name",
            "in_stock",
            "low_stock_alert",
        ]

    def get_in_stock(self, obj):
        return obj.is_active and obj.store.is_active and obj.stock > 0

    def get_low_stock_alert(self, obj):
        if obj.is_active and obj.store.is_active and 0 < obj.stock <= 5:
            return f"Only {obj.stock} left in stock!"
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Handles cart item additions, quantity modifications, and stock validation."""
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.select_related("store__seller__user").all(),
        write_only=True,
    )
    product_detail = CartProductSerializer(source="product", read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
        coerce_to_string=True,
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_detail",
            "quantity",
            "subtotal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        product = attrs.get(
            "product",
            self.instance.product if self.instance else None,
        )
        quantity = attrs.get(
            "quantity",
            self.instance.quantity if self.instance else None,
        )

        if product is not None:
            if not product.is_active or not product.store.is_active:
                raise serializers.ValidationError(
                    {"product": "This product is currently unavailable."}
                )

            if request and request.user == product.store.seller.user:
                raise serializers.ValidationError(
                    {"product": "You cannot purchase your own product."}
                )

            if quantity is not None and quantity > product.stock:
                raise serializers.ValidationError(
                    {"quantity": f"Only {product.stock} items left in stock."}
                )

        return attrs


class CartSerializer(serializers.ModelSerializer):
    """Root serializer representing the user's active shopping cart."""
    cart_items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
        coerce_to_string=True,
    )

    class Meta:
        model = Cart
        fields = [
            "id",
            "cart_items",
            "total_price",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    """Line items for receipts. Uses frozen snapshot fields saved at purchase time."""
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=True
    )
    subtotal = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True, coerce_to_string=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]


class SellerOrderSerializer(serializers.ModelSerializer):
    """Used in Vendor Dashboard and nested inside BuyerOrderSerializer."""
    business_name = serializers.CharField(source="seller.business_name", read_only=True)
    buyer_id = serializers.IntegerField(source="order.user_id", read_only=True)
    shipping_address = serializers.CharField(source="order.shipping_address", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True, coerce_to_string=True
    )

    class Meta:
        model = SellerOrder
        fields = [
            "id",
            "order",
            "buyer_id",
            "business_name",
            "status",
            "shipping_address",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]


class SellerOrderUpdateSerializer(serializers.ModelSerializer):
    """Used exclusively by Sellers via PATCH to update sub-order status."""

    class Meta:
        model = SellerOrder
        fields = ["status"]


class BuyerOrderSerializer(serializers.ModelSerializer):
    """Main receipt presented to Buyers, cleanly grouped by vendor sub-order."""
    seller_orders = SellerOrderSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, read_only=True, coerce_to_string=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "shipping_address",
            "total_amount",
            "seller_orders",
            "created_at",
        ]


class CheckoutSerializer(serializers.Serializer):
    """
    Atomic Multi-Vendor Checkout Engine:
    - Locks cart & product rows to prevent double-checkout race conditions.
    - Locks products in sorted ID order to prevent database deadlocks.
    - Groups items by vendor, generates parent Order + sub SellerOrders.
    - Freezes product prices/names and deducts stock dynamically.
    """
    shipping_address = serializers.CharField(
        required=True,
        max_length=1000,
        error_messages={"blank": "Shipping address cannot be empty."},
    )

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required to checkout.")

        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.cart_items.exists():
            raise serializers.ValidationError({"cart": "Your cart is empty."})

        attrs["cart"] = cart
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        cart = validated_data["cart"]
        shipping_address = validated_data["shipping_address"]

        with transaction.atomic():
            # 1. Lock the cart row so concurrent double-clicks cannot checkout twice
            cart = Cart.objects.select_for_update().get(pk=cart.pk)
            cart_items = list(
                cart.cart_items.select_related("product__store__seller__user")
            )

            if not cart_items:
                raise serializers.ValidationError({"cart": "Your cart is empty."})

            # 2. Lock products in sorted ID order to prevent database deadlocks
            product_ids = sorted(item.product_id for item in cart_items)
            locked_products = {
                p.id: p
                for p in Product.objects.select_for_update()
                .select_related("store__seller__user")
                .filter(id__in=product_ids)
            }

            order_total = Decimal("0.00")
            seller_subtotals = defaultdict(lambda: Decimal("0.00"))
            validated_lines = []

            for item in cart_items:
                product = locked_products[item.product_id]

                if not product.is_active or not product.store.is_active:
                    raise serializers.ValidationError(
                        {"product": f"{product.name} is no longer available."}
                    )

                if product.store.seller.user_id == user.id:
                    raise serializers.ValidationError(
                        {"product": f"You cannot purchase your own product ({product.name})."}
                    )

                if item.quantity > product.stock:
                    raise serializers.ValidationError(
                        {"quantity": f"Only {product.stock} left in stock for {product.name}."}
                    )

                unit_price = product.price
                line_total = unit_price * item.quantity
                order_total += line_total
                seller_subtotals[product.store.seller_id] += line_total
                validated_lines.append((product, item.quantity, unit_price))

            # 3. Create parent Order
            order = Order.objects.create(
                user=user,
                total_amount=order_total,
                shipping_address=shipping_address,
            )

            # 4. Split into one SellerOrder per vendor & build OrderItems
            seller_orders = {}
            order_items_to_create = []

            for product, quantity, unit_price in validated_lines:
                seller = product.store.seller

                if seller.id not in seller_orders:
                    seller_orders[seller.id] = SellerOrder.objects.create(
                        order=order,
                        seller=seller,
                    )

                order_items_to_create.append(
                    OrderItem(
                        order=order,
                        seller_order=seller_orders[seller.id],
                        product=product,
                        product_name=product.name,  # Frozen snapshot title
                        quantity=quantity,
                        unit_price=unit_price,
                    )
                )

                # Deduct inventory stock
                product.stock -= quantity
                product.save(update_fields=["stock"])

            OrderItem.objects.bulk_create(order_items_to_create)

            # 5. Clear the buyer's cart
            cart.cart_items.all().delete()

        # Re-fetch with prefetched relations so BuyerOrderSerializer executes 0 extra queries
        return (
            Order.objects.prefetch_related(
                "seller_orders__seller",
                "seller_orders__items",
            )
            .get(pk=order.pk)
        )


class AdminOrderSerializer(serializers.ModelSerializer):
    """Used only by Superadmins to monitor system-wide orders."""
    username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
        coerce_to_string=True,
    )
    vendor_count = serializers.IntegerField(
        source="seller_orders.count",
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "username",
            "user_email",
            "status",
            "total_amount",
            "vendor_count",
            "shipping_address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "username",
            "user_email",
            "status",
            "total_amount",
            "vendor_count",
            "shipping_address",
            "created_at",
            "updated_at",
        ]