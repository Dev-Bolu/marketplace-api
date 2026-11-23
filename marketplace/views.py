from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ProductFilter
from .models import (
    Cart,
    CartItem,
    Category,
    Order,
    Product,
    SellerOrder,
    SellerProfile,
    Store,
)
from .serializers import (
    AdminOrderSerializer,
    BuyerOrderSerializer,
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    CheckoutSerializer,
    ProductSerializer,
    SellerOrderSerializer,
    SellerOrderUpdateSerializer,
    SellerProfileSerializer,
    StoreSerializer,
    UserRegistrationSerializer,
)


class WelcomeView(APIView):
    def get(self, request):
        return Response({"message": "Welcome to the Marketplace API"})


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def patch(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyCategoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(
            products__store__seller__user=request.user
        ).distinct()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class SellerProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller_profiles = SellerProfile.objects.all()
        serializer = SellerProfileSerializer(seller_profiles, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SellerProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SellerProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        seller_profile = get_object_or_404(SellerProfile, pk=pk)
        serializer = SellerProfileSerializer(seller_profile)
        return Response(serializer.data)


class MySellerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller_profile = get_object_or_404(SellerProfile, user=request.user)
        serializer = SellerProfileSerializer(seller_profile)
        return Response(serializer.data)

    def patch(self, request):
        seller_profile = get_object_or_404(SellerProfile, user=request.user)
        serializer = SellerProfileSerializer(
            seller_profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        seller_profile = get_object_or_404(SellerProfile, user=request.user)
        serializer = SellerProfileSerializer(seller_profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        seller_profile = get_object_or_404(SellerProfile, user=request.user)
        seller_profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StoreListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stores = Store.objects.all()
        serializer = StoreSerializer(stores, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(seller=request.user.sellerprofile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        store = get_object_or_404(Store, pk=pk)
        serializer = StoreSerializer(store)
        return Response(serializer.data)


class MyStoresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stores = Store.objects.filter(seller=request.user.sellerprofile)
        serializer = StoreSerializer(stores, many=True)
        return Response(serializer.data)


class MyStoresDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        store = get_object_or_404(Store, pk=pk, seller=request.user.sellerprofile)
        serializer = StoreSerializer(store)
        return Response(serializer.data)

    def patch(self, request, pk):
        store = get_object_or_404(Store, pk=pk, seller=request.user.sellerprofile)
        serializer = StoreSerializer(store, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        store = get_object_or_404(Store, pk=pk, seller=request.user.sellerprofile)
        serializer = StoreSerializer(store, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        store = get_object_or_404(Store, pk=pk, seller=request.user.sellerprofile)
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductListView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        products = Product.objects.all().order_by("-created_at")
        product_filter = ProductFilter(request.query_params, queryset=products)
        paginator = ProductPagination()
        paginated_products = paginator.paginate_queryset(
            product_filter.qs, request
        )
        serializer = ProductSerializer(paginated_products, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_store = serializer.validated_data["store"]
        authorized_store = get_object_or_404(
            Store, pk=requested_store.pk, seller__user=request.user
        )
        serializer.save(store=authorized_store)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related("store", "category"),
            pk=pk,
            is_active=True,
        )
        serializer = ProductSerializer(product)
        return Response(serializer.data)


class MyProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = (
            Product.objects.filter(store__seller__user=request.user)
            .select_related("store", "category")
            .order_by("-created_at")
        )
        paginator = ProductPagination()
        paginated_products = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(paginated_products, many=True)
        return paginator.get_paginated_response(serializer.data)


class MyProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_product(self, request, pk):
        return get_object_or_404(
            Product, pk=pk, store__seller__user=request.user
        )

    def get(self, request, pk):
        product = self.get_product(request, pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def patch(self, request, pk):
        product = self.get_product(request, pk)
        if "store_id" in request.data:
            return Response(
                {"store_id": "A product cannot be moved to another store."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        product = self.get_product(request, pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Pass context={"request": request} so self-purchase validation executes
        input_serializer = CartItemSerializer(
            data=request.data, context={"request": request}
        )
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        product = input_serializer.validated_data["product"]
        quantity = input_serializer.validated_data["quantity"]
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )

        if created:
            response_status = status.HTTP_201_CREATED
        else:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return Response(
                    {"detail": "Requested quantity exceeds available stock."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.quantity = new_quantity
            cart_item.save()
            response_status = status.HTTP_200_OK

        output_serializer = CartItemSerializer(cart_item)
        return Response(output_serializer.data, status=response_status)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        cart_item = get_object_or_404(
            CartItem, pk=pk, cart__user=request.user
        )
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    def patch(self, request, pk):
        cart_item = get_object_or_404(
            CartItem, pk=pk, cart__user=request.user
        )

        allowed_keys = {"quantity"}
        incoming_keys = set(request.data.keys())

        if not incoming_keys.issubset(allowed_keys):
            return Response(
                {"detail": "Only the 'quantity' field can be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "quantity" not in incoming_keys:
            return Response(
                {"quantity": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CartItemSerializer(
            cart_item,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        cart_item = get_object_or_404(
            CartItem, pk=pk, cart__user=request.user
        )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckoutView(APIView):
    """
    POST /api/orders/checkout/
    Delegates atomic execution, deadlock prevention, and order creation to CheckoutSerializer.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            BuyerOrderSerializer(order).data, status=status.HTTP_201_CREATED
        )


class OrderListView(APIView):
    """GET /api/orders/ -> Returns buyer's order history."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .prefetch_related("seller_orders__items")
            .order_by("-created_at")
        )
        serializer = BuyerOrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = BuyerOrderSerializer(order)
        return Response(serializer.data)

    def patch(self, request, pk):
        data = request.data
        requested_status = data.get("status") if hasattr(data, "get") else None

        if requested_status != Order.StatusChoices.CANCELLED:
            return Response(
                {"detail": "Buyers can only cancel orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(), pk=pk, user=request.user
            )

            if order.status != Order.StatusChoices.PENDING:
                return Response(
                    {"detail": "Only pending orders can be cancelled."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            qty_by_product_id = dict(
                order.order_items.order_by()
                .values("product_id")
                .annotate(total_qty=Sum("quantity"))
                .values_list("product_id", "total_qty")
            )

            now = timezone.now()

            if qty_by_product_id:
                products = list(
                    Product.objects.select_for_update()
                    .filter(pk__in=qty_by_product_id)
                    .order_by("pk")
                )

                if len(products) != len(qty_by_product_id):
                    raise ValidationError(
                        {"detail": "Some products in this order no longer exist."}
                    )

                for product in products:
                    product.stock += qty_by_product_id[product.pk]
                    product.updated_at = now

                Product.objects.bulk_update(products, ["stock", "updated_at"])

            order.status = Order.StatusChoices.CANCELLED
            order.updated_at = now
            order.save(update_fields=["status", "updated_at"])

        serializer = BuyerOrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SellerOrderListView(ListAPIView):
    """GET /api/seller/orders/ -> Vendor views all sub-orders assigned to their store."""

    permission_classes = [IsAuthenticated]
    serializer_class = SellerOrderSerializer

    def get_queryset(self):
        return (
            SellerOrder.objects.filter(seller__user=self.request.user)
            .select_related("order", "seller")
            .prefetch_related("items__product")
            .order_by("-created_at", "-id")
        )


class SellerOrderDetailView(APIView):
    """
    PATCH /api/seller/orders/<pk>/
    Vendor updates status of their sub-order (e.g., PENDING -> SHIPPED).
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        seller_order = get_object_or_404(
            SellerOrder, pk=pk, seller__user=self.request.user
        )
        serializer = SellerOrderUpdateSerializer(
            seller_order, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SellerOrderSerializer(seller_order).data)


class AdminOrderListView(ListAPIView):
    """GET /api/admin/orders/ -> Superadmin view of all platform transactions."""

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminOrderSerializer
    queryset = Order.objects.all().order_by("-created_at")