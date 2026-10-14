from rest_framework.views import APIView
from rest_framework.response import Response

from marketplace.models import Category,Product, SellerProfile, Store, Cart,CartItem
from marketplace.serializers import CategorySerializer, ProductSerializer, SellerProfileSerializer, UserRegistrationSerializer, StoreSerializer, CartSerializer, CartItemSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

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
    
    

class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            store_id = serializer.validated_data.pop("store_id")

            store = get_object_or_404(
                Store,
                pk=store_id,
                seller=request.user.sellerprofile
            )

            serializer.save(store=store)

            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)
    

class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        product = get_object_or_404(Product,pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    
class MyProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(
            store__seller=request.user.sellerprofile
        )
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    

class MyProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        product = get_object_or_404(
            Product,
            pk=pk,
            store__seller=request.user.sellerprofile
        )
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def patch(self, request, pk):
        product = get_object_or_404(
            Product,
            pk=pk,
            store__seller=request.user.sellerprofile
        )

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        product = get_object_or_404(
            Product,
            pk=pk,
            store__seller=request.user.sellerprofile
        )
        serializer = ProductSerializer(
            product,
            data=request.data,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        product = get_object_or_404(
            Product,
            pk=pk,
            store__seller=request.user.sellerprofile
        )
        product.delete()
        return Response(status=204) 
    
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = CartItemSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(cart=cart)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)