from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """
    Grants access only to authenticated users who have an active SellerProfile.
    """
    message = "You must register a Seller Profile to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user 
            and request.user.is_authenticated 
            and hasattr(request.user, "sellerprofile")
        )


class IsStoreOwner(permissions.BasePermission):
    """
    Object-level permission: Allows access only if the store belongs to the logged-in seller.
    """
    message = "You do not have permission to manage this store."

    def has_object_permission(self, request, view, obj):
        return obj.seller.user == request.user


class IsProductOwner(permissions.BasePermission):
    """
    Object-level permission: Allows access only if the product belongs to a store owned by the logged-in seller.
    """
    message = "You do not have permission to modify this product."

    def has_object_permission(self, request, view, obj):
        return obj.store.seller.user == request.user


class IsBuyerOrderOwner(permissions.BasePermission):
    """
    Object-level permission: Allows access only if the order belongs to the requesting buyer.
    """
    message = "You do not have permission to view or modify this order."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsVendorOrderOwner(permissions.BasePermission):
    """
    Object-level permission: Allows access only if the SellerOrder belongs to the requesting vendor's store.
    """
    message = "You do not have permission to manage this vendor order."

    def has_object_permission(self, request, view, obj):
        return obj.seller.user == request.user