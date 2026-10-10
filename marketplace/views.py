from rest_framework.views import APIView
from rest_framework.response import Response

from marketplace.models import Category
from marketplace.serializers import CategorySerializer
from django.shortcuts import get_object_or_404


# Create your views here.
class WelcomeView(APIView):
    def get(self, request):
        return Response({"message": "Welcome to the Marketplace API"})
    

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