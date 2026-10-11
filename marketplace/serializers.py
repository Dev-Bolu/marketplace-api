
from rest_framework import serializers

from rest_framework import serializers
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



class ProductSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = Product
        fields = "__all__"

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


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = "__all__"
        

class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = "__all__"
        read_only_fields = ["user", "created_at"]
    

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = "__all__"
        read_only_fields = ["cart", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = "__all__"
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
    items = OrderItemSerializer(many=True, read_only=True)
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
