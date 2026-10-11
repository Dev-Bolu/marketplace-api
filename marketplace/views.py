from rest_framework.views import APIView
from rest_framework.response import Response

from marketplace.models import Category,Product, SellerProfile
from marketplace.serializers import CategorySerializer, ProductSerializer, SellerProfileSerializer, UserRegistrationSerializer
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
            # What argument should go here?
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)
    
        
    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)

        category.delete()

        return Response(status=204)
    
class ProductListView(APIView):

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)
    

class ProductDetailView(APIView):

    def get(self, request, pk):
        product = get_object_or_404(
            Product,
            pk=pk
        )

        serializer = ProductSerializer(product)
        return Response(serializer.data)
        
        
    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

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
        product = get_object_or_404(Product, pk=pk)

        serializer = ProductSerializer(
            product,
            data=request.data,
            # What argument should go here?
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)
    
        
    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        product.delete()

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