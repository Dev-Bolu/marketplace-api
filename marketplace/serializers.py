from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
    SellerProfile,
    Store,
)


class UserRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "email", "password"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user

class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Category
        fields = "__all__"

    def validate_name(self, value):
        value = value.strip()

        categories = Category.objects.filter(
            name__iexact=value
        )
        if self.instance:
            categories = categories.exclude(
                pk=self.instance.pk
            )
        if categories.exists():
            raise serializers.ValidationError(
                "A category with this name already exists."
            )
        return value


class SellerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = SellerProfile
        fields = [
            "id",
            "username",
            "business_name",
            "phone_number",
            "created_at",
        ]
        read_only_fields = ["created_at"]
    
class StoreSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(
        source="seller.business_name",
        read_only=True
    )

    class Meta:
        model = Store
        fields = "__all__"
        read_only_fields = ["seller", "created_at", "updated_at"]
        


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, updating, and displaying products.

    - store_id is accepted when creating a product.
    - category uses the category slug for a cleaner public API.
    - store ownership is enforced in the view.
    - price and stock are validated before saving.
    """

    store_id = serializers.PrimaryKeyRelatedField(
        source="store",
        queryset=Store.objects.all(),
        write_only=True,
    )

    store = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

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

        read_only_fields = [
            "id",
            "store",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Product name cannot be empty."
            )

        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than zero."
            )

        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Stock cannot be negative."
            )

        return value

class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
    )

    product_detail = ProductSerializer(
        source="product",
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
        coerce_to_string=True,
    )

    class Meta:
        model = CartItem
        fields = "__all__"
        read_only_fields = ["cart", "created_at", "updated_at"]

    def validate(self, attrs):
        # Fallback to existing instance values during partial updates (PATCH)
        product = attrs.get(
            "product", 
            self.instance.product if self.instance else None
        )
        quantity = attrs.get(
            "quantity", 
            self.instance.quantity if self.instance else None
        )

        if product is not None:
            if not product.is_active:
                raise serializers.ValidationError(
                    {"product": "This product is not available."}
                )

            if quantity is not None and quantity > product.stock:
                raise serializers.ValidationError(
                    {"quantity": "Requested quantity exceeds available stock."}
                )

        return attrs


class CartSerializer(serializers.ModelSerializer):
  cart_items = CartItemSerializer(many=True, read_only=True)
  total_price = serializers.DecimalField(
      max_digits=20, decimal_places=2, read_only=True
  )

  class Meta:
    model = Cart

    fields = [
        "id",
        "user",
        "cart_items",
        "total_price",
        "created_at",
        "updated_at",
    ]
    read_only_fields = ["user", "created_at", "updated_at"]

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = [
            "order",
            "unit_price",
            "created_at",
            "updated_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = [
            "user",
            "status",
            "created_at",
            "updated_at",
        ]

class SellerOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    unit_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
        coerce_to_string=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
        coerce_to_string=True,
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "quantity", "unit_price", "subtotal"]


class SellerOrderSerializer(serializers.ModelSerializer):
    # IMPORTANT: serialize ONLY the prefetched filtered list (prevents leaking other sellers' items)
    order_items = SellerOrderItemSerializer(
        source="seller_items",
        many=True,
        read_only=True,
    )
    # Identify the buyer who placed the order.
    buyer_id = serializers.IntegerField(source="user_id", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "buyer_id",
            "order_items",
            "created_at",
            "updated_at",
        ]