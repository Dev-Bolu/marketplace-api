import django_filters
from django.db.models import Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte"
    )

    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte"
    )

    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact"
    )

    search = django_filters.CharFilter(
        method="filter_search"
    )

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    class Meta:
        model = Product
        fields = [
            "min_price",
            "max_price",
            "category",
            "search",
        ]