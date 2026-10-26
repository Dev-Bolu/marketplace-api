
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cart, CartItem, Product, SellerProfile, Store, Order



class CartViewTests(APITestCase):

    def setUp(self):
        # No password hashing is needed because these tests use
        # force_authenticate() rather than logging in.
        self.user = User.objects.create_user(
            username="cartuser",
        )
        self.url = reverse("cart")

    def test_get_creates_empty_cart_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        self.assertFalse(
            Cart.objects.filter(user=self.user).exists()
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            Cart.objects.filter(user=self.user).exists()
        )
        self.assertEqual(response.data["cart_items"], [])
        self.assertEqual(response.data["total_price"], "0.00")

    def test_get_reuses_existing_cart(self):
        self.client.force_authenticate(user=self.user)

        first_response = self.client.get(self.url)
        second_response = self.client.get(self.url)

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            Cart.objects.filter(user=self.user).count(),
            1,
        )
        self.assertEqual(
            first_response.data["id"],
            second_response.data["id"],
        )

    def test_get_cart_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(Cart.objects.count(), 0)

    def test_user_only_sees_their_own_cart(self):
        other_user = User.objects.create_user(
            username="otheruser",
        )
        other_cart = Cart.objects.create(user=other_user)

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertNotEqual(
            response.data["id"],
            other_cart.id,
        )
        self.assertEqual(
            response.data["user"],
            self.user.id,
        )
        self.assertEqual(Cart.objects.count(), 2)
    
    def test_cart_response_includes_total_price_for_multiple_items(self):
        # 1. Create a seller user, seller profile, and store
        seller_user = User.objects.create_user(username="seller")
        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Test Seller",
        )
        store = Store.objects.create(
            seller=seller_profile,
            store_name="Test Store",
        )

        # 2. Create two products with specified prices
        product_a = Product.objects.create(
            store=store,
            name="Product A",
            price=Decimal("100.00"),
            stock=10,
            is_active=True,
        )
        product_b = Product.objects.create(
            store=store,
            name="Product B",
            price=Decimal("50.50"),
            stock=10,
            is_active=True,
        )

        # 3. Create self.user’s cart
        cart = Cart.objects.create(user=self.user)

        # 4. Add items to the cart
        CartItem.objects.create(
            cart=cart,
            product=product_a,
            quantity=2,
        )
        CartItem.objects.create(
            cart=cart,
            product=product_b,
            quantity=3,
        )

        # 5. Authenticate as self.user
        self.client.force_authenticate(user=self.user)

        # 6. GET self.url
        response = self.client.get(self.url)

        # 7. Assert status, item count, and aggregated total price
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["cart_items"]), 2)
        self.assertEqual(response.data["total_price"], "351.50")


class CartItemViewTests(APITestCase):

    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer",
        )

        self.seller_user = User.objects.create_user(
            username="seller",
        )

        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            business_name="Test Seller",
        )

        self.store = Store.objects.create(
            seller=self.seller_profile,
            store_name="Test Store",
        )

        self.product = Product.objects.create(
            store=self.store,
            name="Test Product",
            price=Decimal("100.00"),
            stock=5,
            is_active=True,
        )

        self.url = reverse("cart-item-add")

    def _add(self, product_id=None, quantity=1):
        if product_id is None:
            product_id = self.product.id

        return self.client.post(
            self.url,
            data={
                "product": product_id,
                "quantity": quantity,
            },
            format="json",
        )

    def test_authenticated_user_can_add_product_to_cart(self):
        self.client.force_authenticate(user=self.buyer)

        self.assertFalse(
            Cart.objects.filter(user=self.buyer).exists()
        )

        response = self._add(quantity=2)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        cart = Cart.objects.get(user=self.buyer)
        cart_item = CartItem.objects.get(
            cart=cart,
            product=self.product,
        )

        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(response.data["id"], cart_item.id)
        self.assertEqual(response.data["quantity"], 2)

    def test_add_to_cart_requires_authentication(self):
        response = self._add()

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(Cart.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 0)

    

    def test_cannot_add_inactive_product(self):
        self.product.is_active = False
        self.product.save()

        self.client.force_authenticate(user=self.buyer)

        response = self._add()

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("product", response.data)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_add_nonexistent_product(self):
        self.client.force_authenticate(user=self.buyer)

        response = self._add(product_id=999999)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("product", response.data)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_add_zero_or_negative_quantity(self):
        self.client.force_authenticate(user=self.buyer)

        for quantity in (0, -1):
            with self.subTest(quantity=quantity):
                response = self._add(quantity=quantity)

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn("quantity", response.data)

        self.assertEqual(CartItem.objects.count(), 0)

    def test_adding_same_product_twice_increments_existing_item(self):
        self.client.force_authenticate(user=self.buyer)

        first_response = self._add(quantity=1)
        second_response = self._add(quantity=1)

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        items = CartItem.objects.filter(
            cart__user=self.buyer,
            product=self.product,
        )

        self.assertEqual(items.count(), 1)

        cart_item = items.get()

        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(
            first_response.data["id"],
            second_response.data["id"],
        )
        self.assertEqual(
            second_response.data["quantity"],
            2,
        )

    def test_repeat_add_does_not_exceed_available_stock(self):
        self.client.force_authenticate(user=self.buyer)

        first_response = self._add(quantity=3)
        second_response = self._add(quantity=3)

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("detail", second_response.data)

        cart_item = CartItem.objects.get(
            cart__user=self.buyer,
            product=self.product,
        )

        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(cart_item.quantity, 3)
        self.assertLessEqual(
            cart_item.quantity,
            self.product.stock,
        )

    def test_cannot_add_more_than_available_stock(self):
        self.client.force_authenticate(user=self.buyer)

        # Precondition: Buyer has no cart yet
        self.assertFalse(
            Cart.objects.filter(user=self.buyer).exists()
        )

        response = self._add(quantity=6)  # stock is 5

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("quantity", response.data)
        
        # Postconditions: No cart-items AND no empty cart should be created
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertFalse(
            Cart.objects.filter(user=self.buyer).exists()
        )
    

class CartItemDetailViewTests(APITestCase):

    def setUp(self):
        # 1. Create a buyer (no password hashing overhead)
        self.buyer = User.objects.create_user(username="buyer")

        # 2. Create a seller user (no password hashing overhead)
        self.seller_user = User.objects.create_user(username="seller")

        # 3. Create a seller profile
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            business_name="Test Seller",
        )

        # 4. Create a store
        self.store = Store.objects.create(
            seller=self.seller_profile,
            store_name="Test Store",
        )

        # 5. Create a product
        self.product = Product.objects.create(
            store=self.store,
            name="Test Product",
            price=Decimal("100.00"),
            stock=5,
            is_active=True,
        )

        # 6. Create the buyer's cart
        self.cart = Cart.objects.create(user=self.buyer)

        # 7. Create a cart item with quantity 2
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
        )

        # 8. Build self.url using reverse() with the cart-item primary key
        self.url = reverse(
            "cart-item-detail",
            kwargs={"pk": self.cart_item.pk},
        )

    def test_owner_can_retrieve_cart_item(self):
        self.client.force_authenticate(user=self.buyer)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            self.cart_item.id,
        )
        self.assertEqual(
            response.data["quantity"],
            2,
        )
        self.assertNotIn("product", response.data)
        self.assertEqual(
        response.data["product_detail"]["id"],
        self.product.id,
        )

    def test_other_user_cannot_retrieve_cart_item(self):
        # 1. Create another user without a password
        other_user = User.objects.create_user(username="otherbuyer")

        # 2. Authenticate as that user
        self.client.force_authenticate(user=other_user)

        # 3. GET self.url
        response = self.client.get(self.url)

        # 4. Assert 404 Not Found
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        # 5. Assert the cart item still exists afterward
        self.assertTrue(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )

    def test_owner_can_update_cart_item_quantity(self):
        self.client.force_authenticate(user=self.buyer)

        response = self.client.patch(
            self.url,
            data={"quantity": 4},
            format="json",
        )

        # Assert the response status is 200.
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the response quantity is 4.
        self.assertEqual(response.data["quantity"], 4)

        self.cart_item.refresh_from_db()

        # Assert the database quantity is now 4.
        self.assertEqual(self.cart_item.quantity, 4)

        # Assert there is still exactly one CartItem
        self.assertEqual(CartItem.objects.count(), 1)

    def test_cannot_update_quantity_above_product_stock(self):
        # 1. Authenticate as self.buyer
        self.client.force_authenticate(user=self.buyer)

        # 2. PATCH self.url with quantity 6
        response = self.client.patch(
            self.url,
            data={"quantity": 6},
            format="json",
        )

        # 3. Assert 400 Bad Request
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # 4. Assert "quantity" exists in response.data
        self.assertIn("quantity", response.data)

        # 5. Refresh self.cart_item from the database
        self.cart_item.refresh_from_db()

        # 6. Assert its quantity remains 2
        self.assertEqual(self.cart_item.quantity, 2)

        # 7. Assert only one CartItem exists
        self.assertEqual(CartItem.objects.count(), 1)

    def test_other_user_cannot_update_cart_item(self):
        # 1. Create another user without a password
        other_user = User.objects.create_user(username="otherbuyer")

        # 2. Authenticate as that user
        self.client.force_authenticate(user=other_user)

        # 3. PATCH self.url with the otherwise-valid quantity 4
        response = self.client.patch(
            self.url,
            data={"quantity": 4},
            format="json",
        )

        # 4. Assert 404 Not Found
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        # 5. Refresh self.cart_item from the database
        self.cart_item.refresh_from_db()

        # 6. Assert its quantity is still 2
        self.assertEqual(self.cart_item.quantity, 2)

        # 7. Assert the item still exists
        self.assertTrue(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )

    def test_cannot_update_cart_item_product(self):
        # 1. Create a second active product in self.store
        other_product = Product.objects.create(
            store=self.store,
            name="Other Product",
            price=Decimal("50.00"),
            stock=10,
            is_active=True,
        )

        # 2. Authenticate as self.buyer
        self.client.force_authenticate(user=self.buyer)

        # 3. PATCH self.url with the second product’s ID
        response = self.client.patch(
            self.url,
            data={"product": other_product.id},
            format="json",
        )

        # 4. Assert 400 Bad Request
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # 5. Assert the exact error message guards the allowed-field rule
        self.assertEqual(
            response.data["detail"],
            "Only the 'quantity' field can be updated.",
        )

        # 6. Refresh self.cart_item
        self.cart_item.refresh_from_db()

        # 7. Assert its product_id is still self.product.id
        self.assertEqual(
            self.cart_item.product_id,
            self.product.id,
        )

        # 8. Assert there is still only one cart item
        self.assertEqual(CartItem.objects.count(), 1)

    def test_empty_patch_is_rejected_without_modifying_item(self):
        # 1. Store the original timestamp
        original_updated_at = self.cart_item.updated_at

        # 2. Authenticate as self.buyer
        self.client.force_authenticate(user=self.buyer)

        # 3. PATCH self.url with an empty dictionary
        response = self.client.patch(
            self.url,
            data={},
            format="json",
        )

        # 4. Assert 400 Bad Request
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # 5. Assert the response flags the missing quantity field
        self.assertEqual(
            response.data,
            {"quantity": ["This field is required."]},
        )

        # 6. Refresh the item from the database
        self.cart_item.refresh_from_db()

        # 7. Assert quantity remains 2
        self.assertEqual(self.cart_item.quantity, 2)

        # 8. Assert updated_at still equals original_updated_at
        self.assertEqual(
            self.cart_item.updated_at,
            original_updated_at,
        )
    
    def test_owner_can_delete_cart_item(self):
        # 1. Authenticate as self.buyer
        self.client.force_authenticate(user=self.buyer)

        # 2. DELETE self.url
        response = self.client.delete(self.url)

        # 3. Assert 204 No Content
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        # 4. Assert the cart item no longer exists
        self.assertFalse(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )

        # 5. Assert the buyer’s cart still exists
        self.assertTrue(
            Cart.objects.filter(user=self.buyer).exists()
        )

        # 6. Assert the product still exists
        self.assertTrue(
            Product.objects.filter(pk=self.product.pk).exists()
        )

    def test_other_user_cannot_delete_cart_item(self):
        # 1. Create another user without a password
        other_user = User.objects.create_user(username="otherbuyer")

        # 2. Authenticate as that user
        self.client.force_authenticate(user=other_user)

        # 3. DELETE self.url
        response = self.client.delete(self.url)

        # 4. Assert 404 Not Found
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        # 5. Assert the cart item still exists
        self.assertTrue(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )

        # 6. Refresh the item and assert its quantity is still 2
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)

    def test_cart_item_detail_requires_authentication(self):
        # 1. Do not call force_authenticate() to keep the request anonymous

        # 2. GET self.url
        response = self.client.get(self.url)

        # 3. Assert 401 Unauthorized
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        # 4. Assert the cart item still exists
        self.assertTrue(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )

    def test_cart_item_response_includes_correct_subtotal(self):
        # 1. Authenticate as self.buyer
        self.client.force_authenticate(user=self.buyer)

        # 2. GET self.url
        response = self.client.get(self.url)

        # 3. Assert 200 OK
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        # 4. Assert subtotal matches the expected formatted decimal string
        self.assertEqual(
            response.data["subtotal"],
            "200.00",
        )

class OrderListViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="buyer")
        self.url = reverse("order-list")

    def test_cannot_checkout_without_a_cart(self):
        self.client.force_authenticate(user=self.user)

        # Confirm the request starts with no cart or order.
        self.assertFalse(
            Cart.objects.filter(user=self.user).exists()
        )
        self.assertFalse(
            Order.objects.filter(user=self.user).exists()
        )

        response = self.client.post(
            self.url,
            data={},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data,
            {"detail": "Cannot checkout an empty cart."},
        )

        # A failed checkout should not modify the database.
        self.assertFalse(
            Cart.objects.filter(user=self.user).exists()
        )
        self.assertFalse(
            Order.objects.filter(user=self.user).exists()
        )
    
    def test_cannot_checkout_existing_empty_cart(self):
    # Arrange: the user already has a cart, but it contains no items.
        cart = Cart.objects.create(user=self.user)

        self.client.force_authenticate(user=self.user)

        # Act
        response = self.client.post(
            self.url,
            data={},
            format="json",
        )

        # Assert: checkout is rejected.
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data,
            {"detail": "Cannot checkout an empty cart."},
        )

        # The same cart still exists and no order was created.
        self.assertTrue(
            Cart.objects.filter(
                pk=cart.pk,
                user=self.user,
            ).exists()
        )
        self.assertEqual(
            Cart.objects.filter(user=self.user).count(),
            1,
        )
        self.assertFalse(
            Order.objects.filter(user=self.user).exists()
        )
    
    def test_checkout_rejects_inactive_product(self):
        seller_user = User.objects.create_user(
            username="inactive-seller",
        )

        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Inactive Seller",
        )

        store = Store.objects.create(
            seller=seller_profile,
            store_name="Inactive Store",
        )

        product = Product.objects.create(
            store=store,
            name="Inactive Product",
            price=Decimal("100.00"),
            stock=10,
            is_active=False,
        )

        cart = Cart.objects.create(
            user=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            self.url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"],
            "Inactive Product is no longer available.",
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )
        
    def test_checkout_rejects_insufficient_stock(self):
        seller_user = User.objects.create_user(
            username="stock-seller",
        )

        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Stock Seller",
        )

        store = Store.objects.create(
            seller=seller_profile,
            store_name="Stock Store",
        )

        product = Product.objects.create(
            store=store,
            name="Limited Product",
            price=Decimal("100.00"),
            stock=2,
            is_active=True,
        )

        cart = Cart.objects.create(
            user=self.user,
        )

        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=5,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            self.url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"],
            "Not enough stock for Limited Product. Available stock: 2.",
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

        product.refresh_from_db()

        self.assertEqual(
            product.stock,
            2,
        )

        cart_item.refresh_from_db()

        self.assertEqual(
            cart_item.quantity,
            5,
        )
    
    def test_checkout_saves_current_product_price(self):
        seller_user = User.objects.create_user(
            username="price-seller",
        )

        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Price Seller",
        )

        store = Store.objects.create(
            seller=seller_profile,
            store_name="Price Store",
        )

        product = Product.objects.create(
            store=store,
            name="Price Snapshot Product",
            price=Decimal("100.00"),
            stock=10,
            is_active=True,
        )

        cart = Cart.objects.create(
            user=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            self.url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.user,
        )

        order_item = order.order_items.get(
            product=product,
        )

        self.assertEqual(
            order_item.unit_price,
            Decimal("100.00"),
        )
    
    def test_successful_checkout_empties_cart(self):
        seller_user = User.objects.create_user(
            username="cart-seller",
        )

        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Cart Seller",
        )

        store = Store.objects.create(
            seller=seller_profile,
            store_name="Cart Store",
        )

        product = Product.objects.create(
            store=store,
            name="Cart Product",
            price=Decimal("100.00"),
            stock=10,
            is_active=True,
        )

        cart = Cart.objects.create(
            user=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            self.url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        cart.refresh_from_db()

        self.assertEqual(
            cart.cart_items.count(),
            0,
        )

        self.assertTrue(
            Order.objects.filter(
                user=self.user,
            ).exists()
        )
        
    def test_checkout_creates_order_with_multiple_products(self):
        seller_user = User.objects.create_user(
            username="multi-seller",
        )

        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Multi Seller",
        )

        store = Store.objects.create(
            seller=seller_profile,
            store_name="Multi Store",
        )

        product_one = Product.objects.create(
            store=store,
            name="Product One",
            price=Decimal("100.00"),
            stock=10,
            is_active=True,
        )

        product_two = Product.objects.create(
            store=store,
            name="Product Two",
            price=Decimal("200.00"),
            stock=8,
            is_active=True,
        )

        cart = Cart.objects.create(
            user=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            product=product_one,
            quantity=2,
        )

        CartItem.objects.create(
            cart=cart,
            product=product_two,
            quantity=3,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            self.url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.user,
        )

        self.assertEqual(
            order.order_items.count(),
            2,
        )

        item_one = order.order_items.get(
            product=product_one,
        )

        item_two = order.order_items.get(
            product=product_two,
        )

        self.assertEqual(
            item_one.quantity,
            2,
        )

        self.assertEqual(
            item_one.unit_price,
            Decimal("100.00"),
        )

        self.assertEqual(
            item_two.quantity,
            3,
        )

        self.assertEqual(
            item_two.unit_price,
            Decimal("200.00"),
        )

        product_one.refresh_from_db()
        product_two.refresh_from_db()

        self.assertEqual(
            product_one.stock,
            8,
        )

        self.assertEqual(
            product_two.stock,
            5,
        )
    def test_order_total_price_is_calculated_correctly(self):
        seller_user = User.objects.create_user(
            username="total-seller",
        )

        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Total Seller",
        )

        store = Store.objects.create(
            seller=seller_profile,
            store_name="Total Store",
        )

        product_one = Product.objects.create(
            store=store,
            name="Product One",
            price=Decimal("100.00"),
            stock=10,
            is_active=True,
        )

        product_two = Product.objects.create(
            store=store,
            name="Product Two",
            price=Decimal("200.00"),
            stock=10,
            is_active=True,
        )

        cart = Cart.objects.create(
            user=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            product=product_one,
            quantity=2,
        )

        CartItem.objects.create(
            cart=cart,
            product=product_two,
            quantity=3,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            self.url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.user,
        )

        self.assertEqual(
            order.total_price,
            Decimal("800.00"),
        )
    
    def test_buyer_can_cancel_pending_order_and_stock_is_restored(self):
        seller_user = User.objects.create_user(
            username="cancel-seller",
        )

        seller_profile = SellerProfile.objects.create(
            user=seller_user,
            business_name="Cancel Seller",
        )

        store = Store.objects.create(
            seller=seller_profile,
            store_name="Cancel Store",
        )

        product = Product.objects.create(
            store=store,
            name="Cancel Product",
            price=Decimal("100.00"),
            stock=10,
            is_active=True,
        )

        cart = Cart.objects.create(user=self.user)

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=3,
        )

        # Checkout first.
        self.client.force_authenticate(user=self.user)

        checkout_response = self.client.post(
            self.url,
            format="json",
        )

        self.assertEqual(
            checkout_response.status_code,
            status.HTTP_201_CREATED,
        )

        product.refresh_from_db()

        # 10 - 3 = 7 after checkout.
        self.assertEqual(product.stock, 7)

        order = Order.objects.get(user=self.user)

        # Cancel the order.
        response = self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"status": Order.OrderStatus.CANCELLED},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        order.refresh_from_db()
        product.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.OrderStatus.CANCELLED,
        )

        # 7 + 3 = 10 after cancellation.
        self.assertEqual(product.stock, 10)
    
    def _checkout_pending_order(self, quantity=3, stock=10):
        seller_user = User.objects.create_user(username=f"seller-{quantity}-{stock}")
        seller_profile = SellerProfile.objects.create(user=seller_user, business_name="S")
        store = Store.objects.create(seller=seller_profile, store_name="St")
        product = Product.objects.create(
            store=store, name="P", price=Decimal("100.00"), stock=stock, is_active=True
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        return product, Order.objects.get(user=self.user)

    def _cancel(self, order):
        return self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"status": Order.OrderStatus.CANCELLED},
            format="json",
        )

    def test_cancelling_twice_restores_stock_only_once(self):
        product, order = self._checkout_pending_order()

        self.assertEqual(self._cancel(order).status_code, status.HTTP_200_OK)
        self.assertEqual(self._cancel(order).status_code, status.HTTP_400_BAD_REQUEST)

        product.refresh_from_db()
        self.assertEqual(product.stock, 10)

    def test_non_pending_order_cannot_be_cancelled(self):
        product, order = self._checkout_pending_order()
        Order.objects.filter(pk=order.pk).update(status=Order.OrderStatus.SHIPPED)

        self.assertEqual(self._cancel(order).status_code, status.HTTP_400_BAD_REQUEST)

        product.refresh_from_db()
        self.assertEqual(product.stock, 7)

    def test_cannot_cancel_another_users_order(self):
        product, order = self._checkout_pending_order()
        other = User.objects.create_user(username="other-buyer")
        self.client.force_authenticate(user=other)

        self.assertEqual(self._cancel(order).status_code, status.HTTP_404_NOT_FOUND)

        product.refresh_from_db()
        self.assertEqual(product.stock, 7)

    def test_rejects_non_cancel_status(self):
        _, order = self._checkout_pending_order()
        resp = self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"status": "shipped"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
class ProductWriteTests(APITestCase):

    def setUp(self):
        self.seller_user = User.objects.create_user(
            username="product-seller",
        )

        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            business_name="Product Seller",
        )

        self.store = Store.objects.create(
            seller=self.seller_profile,
            store_name="Product Store",
        )

        self.url = reverse("product-list")


    def test_seller_can_create_product_in_own_store(self):
        self.client.force_authenticate(user=self.seller_user)

        payload = {
            "store_id": self.store.id,
            "name": "Test Product",
            "description": "Test description",
            "price": "100.00",
            "stock": 5,
            "is_active": True,
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        product = Product.objects.get(
            name="Test Product",
        )

        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(product.store, self.store)
        self.assertEqual(product.price, Decimal("100.00"))
        self.assertEqual(product.stock, 5)
        self.assertTrue(product.is_active)
        
    def test_seller_cannot_create_product_in_another_seller_store(self):
        other_user = User.objects.create_user(
            username="other-seller",
        )

        other_profile = SellerProfile.objects.create(
            user=other_user,
            business_name="Other Seller",
        )

        other_store = Store.objects.create(
            seller=other_profile,
            store_name="Other Store",
        )

        self.client.force_authenticate(user=self.seller_user)

        payload = {
            "store_id": other_store.id,
            "name": "Unauthorized Product",
            "description": "Should not be created",
            "price": "100.00",
            "stock": 5,
            "is_active": True,
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            Product.objects.filter(
                name="Unauthorized Product",
            ).exists()
        )
        
    def test_seller_cannot_access_another_sellers_product(self):
        product = Product.objects.create(
            store=self.store,
            name="Private Product",
            description="Seller A product",
            price=Decimal("100.00"),
            stock=10,
        )

        other_user = User.objects.create_user(
            username="other-seller",
        )

        self.client.force_authenticate(user=other_user)

        url = reverse(
            "my-product-detail",
            kwargs={"pk": product.id},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        
    def test_seller_cannot_update_another_sellers_product(self):
        product = Product.objects.create(
            store=self.store,
            name="Private Product",
            description="Seller A product",
            price=Decimal("100.00"),
            stock=10,
        )

        other_user = User.objects.create_user(
            username="other-seller",
        )

        self.client.force_authenticate(user=other_user)

        url = reverse(
            "my-product-detail",
            kwargs={"pk": product.id},
        )

        response = self.client.patch(
            url,
            data={"price": "50.00"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        product.refresh_from_db()

        self.assertEqual(
            product.price,
            Decimal("100.00"),
        )
    
    def test_seller_cannot_delete_another_sellers_product(self):
        product = Product.objects.create(
            store=self.store,
            name="Protected Product",
            description="Seller A product",
            price=Decimal("100.00"),
            stock=10,
        )

        other_user = User.objects.create_user(
            username="other-seller",
        )

        self.client.force_authenticate(user=other_user)

        url = reverse(
            "my-product-detail",
            kwargs={"pk": product.id},
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Product.objects.filter(
                pk=product.id,
            ).exists()
        )
    
    def test_seller_can_delete_own_product(self):
        product = Product.objects.create(
            store=self.store,
            name="Product To Delete",
            description="My product",
            price=Decimal("100.00"),
            stock=10,
        )

        self.client.force_authenticate(
            user=self.seller_user,
        )

        url = reverse(
            "my-product-detail",
            kwargs={"pk": product.id},
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Product.objects.filter(
                pk=product.id,
            ).exists()
        )

class StoreWriteTests(APITestCase):

    def setUp(self):
        self.seller_user = User.objects.create_user(
            username="store-seller",
        )

        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            business_name="Store Seller",
        )

        self.url = reverse("store-list")

    def test_seller_can_create_store(self):
        self.client.force_authenticate(
            user=self.seller_user,
        )

        payload = {
            "store_name": "My New Store",
            "description": "My marketplace store",
            "location": "Lagos",
            "is_active": True,
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        store = Store.objects.get(
            store_name="My New Store",
        )

        self.assertEqual(
            store.seller,
            self.seller_profile,
        )
        
    def test_seller_can_access_own_store(self):
        store = Store.objects.create(
            seller=self.seller_profile,
            store_name="My Store",
        )

        self.client.force_authenticate(
            user=self.seller_user,
        )

        url = reverse(
            "my-stores-detail",
            kwargs={"pk": store.id},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["store_name"],
            "My Store",
        )

    def test_seller_cannot_access_another_sellers_store(self):
        other_user = User.objects.create_user(
            username="other-seller",
        )

        other_profile = SellerProfile.objects.create(
            user=other_user,
            business_name="Other Seller",
        )

        other_store = Store.objects.create(
            seller=other_profile,
            store_name="Other Store",
        )

        self.client.force_authenticate(
            user=self.seller_user,
        )

        url = reverse(
            "my-stores-detail",
            kwargs={"pk": other_store.id},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        
    def test_seller_cannot_update_another_sellers_store(self):
        other_user = User.objects.create_user(
            username="other-seller",
        )

        other_profile = SellerProfile.objects.create(
            user=other_user,
            business_name="Other Seller",
        )

        other_store = Store.objects.create(
            seller=other_profile,
            store_name="Other Store",
        )

        self.client.force_authenticate(
            user=self.seller_user,
        )

        url = reverse(
            "my-stores-detail",
            kwargs={"pk": other_store.id},
        )

        response = self.client.patch(
            url,
            data={
                "store_name": "Hacked Store",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        other_store.refresh_from_db()

        self.assertEqual(
            other_store.store_name,
            "Other Store",
        )
        
    def test_seller_cannot_delete_another_sellers_store(self):
        other_user = User.objects.create_user(
            username="other-seller",
        )

        other_profile = SellerProfile.objects.create(
            user=other_user,
            business_name="Other Seller",
        )

        other_store = Store.objects.create(
            seller=other_profile,
            store_name="Other Store",
        )

        self.client.force_authenticate(
            user=self.seller_user,
        )

        url = reverse(
            "my-stores-detail",
            kwargs={"pk": other_store.id},
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Store.objects.filter(
                pk=other_store.id,
            ).exists()
        )
    
    def test_seller_can_update_own_store(self):
        store = Store.objects.create(
            seller=self.seller_profile,
            store_name="Old Store Name",
        )

        self.client.force_authenticate(
            user=self.seller_user,
        )

        url = reverse(
            "my-stores-detail",
            kwargs={"pk": store.id},
        )

        response = self.client.patch(
            url,
            data={
                "store_name": "New Store Name",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        store.refresh_from_db()

        self.assertEqual(
            store.store_name,
            "New Store Name",
        )
        
    def test_seller_can_delete_own_store(self):
        store = Store.objects.create(
            seller=self.seller_profile,
            store_name="Store To Delete",
        )

        self.client.force_authenticate(
            user=self.seller_user,
        )

        url = reverse(
            "my-stores-detail",
            kwargs={"pk": store.id},
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Store.objects.filter(
                pk=store.id,
            ).exists()
        )
        
class UserRegistrationTests(APITestCase):

    def setUp(self):
        self.url = reverse("user-register")

    def test_user_can_register(self):
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123",
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            User.objects.filter(
                username="newuser",
            ).exists()
        )

    def test_password_is_hashed(self):
        payload = {
            "username": "secureuser",
            "email": "secure@example.com",
            "password": "StrongPassword123",
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = User.objects.get(
            username="secureuser",
        )

        self.assertNotEqual(
            user.password,
            "StrongPassword123",
        )

        self.assertTrue(
            user.check_password("StrongPassword123")
        )

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPassword123",
        )

        payload = {
            "username": "existinguser",
            "email": "another@example.com",
            "password": "StrongPassword123",
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            User.objects.filter(
                username="existinguser",
            ).count(),
            1,
        )
        
class JWTAuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="jwtuser",
            password="StrongPassword123",
        )
        self.url = reverse("token-obtain-pair")

    def test_valid_credentials_return_tokens(self):
        payload = {
            "username": "jwtuser",
            "password": "StrongPassword123",
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_invalid_password_is_rejected(self):
        payload = {
            "username": "jwtuser",
            "password": "WrongPassword123",
        }

        response = self.client.post(
            self.url,
            data=payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_protected_endpoint_requires_authentication(self):
        url = reverse("cart")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_valid_token_can_access_protected_endpoint(self):
        token_response = self.client.post(
            self.url,
            data={
                "username": "jwtuser",
                "password": "StrongPassword123",
            },
            format="json",
        )

        access_token = token_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            reverse("cart")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )