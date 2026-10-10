from rest_framework.views import APIView
from rest_framework.response import Response

from marketplace.models import Category
from marketplace.serializers import CategorySerializer


# Create your views here.
class WelcomeView(APIView):
    def get(self, request):
        return Response({"message": "Welcome to the Marketplace API"})
    

class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)