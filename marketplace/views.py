from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from marketplace.models import Category,Product, SellerProfile, Store, Cart,CartItem,Order, OrderItem
from .serializers import CategorySerializer, ProductSerializer, SellerProfileSerializer, UserRegistrationSerializer, StoreSerializer, CartSerializer, CartItemSerializer,OrderSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from .filters import ProductFilter
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Prefetch, Exists, OuterRef
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from rest_framework.generics import ListAPIView
from .serializers import SellerOrderSerializer



# Create your views here.
class WelcomeView(APIView):
    def get(self, request):
        return Response({"message": "Welcome to the Marketplace API"})

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

class CategoryListView(APIView):

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)
    

class CategoryDetailView(APIView):

    def get(self, request, pk):
        category = get_object_or_404(
            Category,
            pk=pk
        )

        serializer = CategorySerializer(category)
        return Response(serializer.data)
        
        
    def patch(self, request, pk):
        category = get_object_or_404(Category, pk=pk)

        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)
        
        
    def put(self, request, pk):
        category = get_object_or_404(Category, pk=pk)

        serializer = CategorySerializer(
            category,
            data=request.data,
            
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)
    
        
    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)

        category.delete()

        return Response(status=204)
    
class SellerProfileListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        seller_profiles = SellerProfile.objects.all()
        serializer = SellerProfileSerializer(
            seller_profiles,
            many=True
        )
        return Response(serializer.data)
    def post(self, request):
        serializer = SellerProfileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

class SellerProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        seller_profile = get_object_or_404(
            SellerProfile,
            pk=pk
        )

        serializer = SellerProfileSerializer(seller_profile)
        return Response(serializer.data)


class MySellerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller_profile = get_object_or_404(
            SellerProfile,
            user=request.user
        )
        serializer = SellerProfileSerializer(seller_profile)
        return Response(serializer.data)
    def patch(self, request):
        seller_profile = get_object_or_404(
            SellerProfile,
            user=request.user
        )
        serializer = SellerProfileSerializer(
            seller_profile,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    def put(self, request):
        seller_profile = get_object_or_404(
            SellerProfile,
            user=request.user
        )
        serializer = SellerProfileSerializer(
            seller_profile,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    def delete(self, request):
        seller_profile = get_object_or_404(
            SellerProfile,
            user=request.user
        )
        seller_profile.delete()
        return Response(status=204)
    
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
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

class StoreDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk):
        store = get_object_or_404(Store,pk=pk)
        serializer = StoreSerializer(store)
        return Response(serializer.data)
    
        
class MyStoresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stores = Store.objects.filter(
            seller=request.user.sellerprofile
        )

        serializer = StoreSerializer(
            stores,
            many=True
        )

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
        return Response(serializer.errors, status=400)
                    
    def put(self, request, pk):
        store = get_object_or_404(Store, pk=pk, seller=request.user.sellerprofile)
        serializer = StoreSerializer(
            store,
            data=request.data,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
            
    def delete(self, request, pk):
        store = get_object_or_404(Store, pk=pk, seller=request.user.sellerprofile)
        store.delete()
        return Response(status=204)  
    
    
class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return [IsAuthenticated()]


    def get(self, request):
        products = Product.objects.all().order_by("-created_at")

        product_filter = ProductFilter(
            request.query_params,
            queryset=products,
        )

        paginator = ProductPagination()

        paginated_products = paginator.paginate_queryset(
            product_filter.qs,
            request,
        )

        serializer = ProductSerializer(
            paginated_products,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_store = serializer.validated_data["store"]

        # Security: seller may only create products in their own store.
        authorized_store = get_object_or_404(
            Store,
            pk=requested_store.pk,
            seller__user=request.user,
        )

        serializer.save(store=authorized_store)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )
    

class ProductDetailView(APIView):
    """
    Public endpoint for viewing a single product.

    Authentication is not required because customers should
    be able to browse product details before logging in.
    """

    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related(
                "store",
                "category",
            ),
            pk=pk,
            is_active=True,
        )

        serializer = ProductSerializer(product)

        return Response(serializer.data)
    
class MyProductListView(APIView):
    """
    Returns products belonging only to the authenticated seller.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = (
            Product.objects
            .filter(store__seller__user=request.user)
            .select_related("store", "category")
            .order_by("-created_at")
        )

        paginator = ProductPagination()

        paginated_products = paginator.paginate_queryset(
            products,
            request,
        )

        serializer = ProductSerializer(
            paginated_products,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )
    

class MyProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_product(self, request, pk):
        return get_object_or_404(
            Product,
            pk=pk,
            store__seller__user=request.user,
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

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        product = self.get_product(request, pk)
        product.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
    
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart,_ = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate input before making database changes.
        input_serializer = CartItemSerializer(data=request.data)

        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = input_serializer.validated_data["product"]
        quantity = input_serializer.validated_data["quantity"]

        # Create the cart only after the input has passed validation.
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if created:
            response_status = status.HTTP_201_CREATED
        else:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.stock:
                return Response(
                    {
                        "detail":
                        "Requested quantity exceeds available stock."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item.quantity = new_quantity
            cart_item.save()

            response_status = status.HTTP_200_OK

        output_serializer = CartItemSerializer(cart_item)

        return Response(
            output_serializer.data,
            status=response_status,
        )

class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        cart_item = get_object_or_404(
            CartItem,
            pk=pk,
            cart__user=request.user
        )
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    def patch(self, request, pk):
        # Retrieve only an item belonging to the authenticated user.
        cart_item = get_object_or_404(
            CartItem,
            pk=pk,
            cart__user=request.user,
        )

        allowed_keys = {"quantity"}
        incoming_keys = set(request.data.keys())

        # Reject fields other than quantity.
        if not incoming_keys.issubset(allowed_keys):
            return Response(
                {"detail": "Only the 'quantity' field can be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent an empty PATCH request.
        if "quantity" not in incoming_keys:
            return Response(
                {"quantity": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CartItemSerializer(
            cart_item,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        cart_item = get_object_or_404(
            CartItem,
            pk=pk,
            cart__user=request.user
        )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = request.user.orders.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user

        cart = Cart.objects.filter(user=user).first()

        if cart is None:
            return Response(
                {"detail": "Cannot checkout an empty cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_items = cart.cart_items.all()

        if not cart_items.exists():
            return Response(
                {"detail": "Cannot checkout an empty cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():

            # Lock and validate every product
            products = {}

            for cart_item in cart_items:
                product = Product.objects.select_for_update().get(
                    pk=cart_item.product_id
                )

                if not product.is_active:
                    return Response(
                        {"error": f"{product.name} is no longer available."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if cart_item.quantity > product.stock:
                    return Response(
                        {
                            "error": (
                                f"Not enough stock for {product.name}. "
                                f"Available stock: {product.stock}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                products[product.id] = product

            # Create the order
            order = Order.objects.create(
                user=user,
                status=Order.OrderStatus.PENDING
            )

            # Create the order items
            order_items = []

            for cart_item in cart_items:
                product = products[cart_item.product_id]

                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=cart_item.quantity,
                        unit_price=product.price
                    )
                )

                # Reduce stock
                product.stock -= cart_item.quantity
                product.save(update_fields=["stock"])

            OrderItem.objects.bulk_create(order_items)

            # Clear the buyer's cart
            cart_items.delete()

        serializer = OrderSerializer(order)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request, pk):
        order = get_object_or_404(
            Order,
            pk=pk,
            user=request.user,
        )
 
        serializer = OrderSerializer(order)
 
        return Response(serializer.data)
 
    def patch(self, request, pk):
        # Guard against non-dict bodies (e.g. a JSON array), which
        # would otherwise raise AttributeError and return a 500.
        data = request.data
        requested_status = data.get("status") if hasattr(data, "get") else None
 
        # Buyers are only allowed to request cancellation.
        if requested_status != Order.OrderStatus.CANCELLED:
            return Response(
                {"detail": "Buyers can only cancel orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        with transaction.atomic():
 
            # Lock the order so two cancellation requests
            # cannot process the same order simultaneously.
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=pk,
                user=request.user,
            )
 
            # Only pending orders can be cancelled.
            if order.status != Order.OrderStatus.PENDING:
                return Response(
                    {"detail": "Only pending orders can be cancelled."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
 
            # Total quantity ordered per product.
            # .order_by() clears any default Meta.ordering so the
            # GROUP BY yields exactly one row per product.
            qty_by_product_id = dict(
                order.order_items
                .order_by()
                .values("product_id")
                .annotate(total_qty=Sum("quantity"))
                .values_list("product_id", "total_qty")
            )
 
            now = timezone.now()
 
            if qty_by_product_id:
 
                # Lock all affected products in one query, ordered by pk
                # so every code path acquires locks in the same order
                # (reduces deadlock risk).
                products = list(
                    Product.objects
                    .select_for_update()
                    .filter(pk__in=qty_by_product_id)
                    .order_by("pk")
                )
 
                # Defensive check in case an order references
                # a product that no longer exists. Raising DRF's
                # ValidationError rolls back the transaction and
                # produces a 400 response.
                if len(products) != len(qty_by_product_id):
                    raise ValidationError(
                        {"detail": "Some products in this order no longer exist."}
                    )
 
                # Restore the ordered quantities to stock.
                for product in products:
                    product.stock += qty_by_product_id[product.pk]
                    # bulk_update does not trigger auto_now fields.
                    product.updated_at = now
 
                Product.objects.bulk_update(
                    products,
                    ["stock", "updated_at"],
                )
 
            # Finally mark the order as cancelled.
            order.status = Order.OrderStatus.CANCELLED
            order.updated_at = now
 
            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )
 
        serializer = OrderSerializer(order)
 
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class SellerOrderListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SellerOrderSerializer

    from django.db.models import Exists, OuterRef, Prefetch

    def get_queryset(self):
        user = self.request.user

        # Used for prefetch (ordering is fine here)
        seller_items_qs = (
            OrderItem.objects
            .filter(product__store__seller__user=user)
            .select_related("product")
            .order_by("id")
        )

        # Used only for EXISTS (no ordering)
        seller_items_exists_qs = (
            OrderItem.objects
            .filter(
                order=OuterRef("pk"),
                product__store__seller__user=user,
            )
            .order_by()  # important: clear ordering in subquery
        )

        return (
            Order.objects
            .annotate(has_seller_items=Exists(seller_items_exists_qs))
            .filter(has_seller_items=True)
            .order_by("-created_at", "-id")
            .prefetch_related(
                Prefetch("order_items", queryset=seller_items_qs, to_attr="seller_items")
            )
        )