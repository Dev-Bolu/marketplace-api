"""
Optimized cart / order / store / product test suite.

Why this is fast
----------------
1. setUpTestData() builds each fixture graph ONCE per class. Django wraps
   every test in a nested transaction that rolls back to this snapshot, so
   primary keys stay stable and ~70% of fixture INSERTs disappear entirely.
2. Rows shared by several tests (other_user, other_store, a shared product)
   are hoisted to class level instead of being rebuilt in every test.
3. force_authenticate() runs once in setUp(); anonymous tests opt out with
   force_authenticate(user=None).
4. Factory helpers (make_store / make_product / cart_with_items) keep
   per-test writes limited to the rows that actually vary, and bulk_create()
   writes multi-item carts in a single INSERT.
5. Password hashing -- the suite's silent killer (every create_user with a
   password, every check_password, every token obtain = one PBKDF2 round of
   ~600k iterations) -- is cut to the two fixtures that truly need it, and
   settings/test.py swaps PBKDF2 for MD5PasswordHasher. Microseconds.

Run with:
    DJANGO_SETTINGS_MODULE=settings.test python manage.py test --keepdb --parallel

NOTE (setUpTestData semantics): instances assigned to class attributes are
deep-copied per test, so mutating self.product inside a test cannot leak
into other tests -- but always assert against the DATABASE
(refresh_from_db() / objects.get()), never against stale in-memory state.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cart, CartItem, Order, Product, SellerProfile, Store


# ---------------------------------------------------------------------------
# Factory helpers -- the only per-test writes most tests need.
# ---------------------------------------------------------------------------

def make_store(username="seller", business_name="Seller", store_name="Store"):
    """user -> SellerProfile -> Store in three INSERTs."""
    user = User.objects.create_user(username=username)
    profile = SellerProfile.objects.create(
        user=user, business_name=business_name
    )
    return Store.objects.create(seller=profile, store_name=store_name)


def make_product(store, name="Product", price="100.00", stock=10, is_active=True):
    return Product.objects.create(
        store=store,
        name=name,
        price=Decimal(price),
        stock=stock,
        is_active=is_active,
    )


def cart_with_items(user, *items):
    """Create a cart plus all items in 2 queries: ((product, qty), ...)."""
    cart = Cart.objects.create(user=user)
    CartItem.objects.bulk_create(
        CartItem(cart=cart, product=product, quantity=quantity)
        for product, quantity in items
    )
    return cart


class CartViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # One user + one URL for the whole class: 1 INSERT instead of 5.
        cls.user = User.objects.create_user(username="cartuser")
        cls.url = reverse("cart")

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_creates_empty_cart_for_authenticated_user(self):
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Cart.objects.filter(user=self.user).exists())
        self.assertEqual(response.data["cart_items"], [])
        self.assertEqual(response.data["total_price"], "0.00")

    def test_get_reuses_existing_cart(self):
        first_response = self.client.get(self.url)
        second_response = self.client.get(self.url)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)
        self.assertEqual(first_response.data["id"], second_response.data["id"])

    def test_get_cart_requires_authentication(self):
        self.client.force_authenticate(user=None)  # opt out of setUp auth

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Cart.objects.count(), 0)

    def test_user_only_sees_their_own_cart(self):
        other_cart = Cart.objects.create(
            user=User.objects.create_user(username="otheruser")
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data["id"], other_cart.id)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(Cart.objects.count(), 2)

    def test_cart_response_includes_total_price_for_multiple_items(self):
        store = make_store()
        product_a = make_product(store, name="Product A", price="100.00")
        product_b = make_product(store, name="Product B", price="50.50")
        cart_with_items(self.user, (product_a, 2), (product_b, 3))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["cart_items"]), 2)
        self.assertEqual(response.data["total_price"], "351.50")


class CartItemViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # The whole buyer -> store -> product graph: built once, not 8x.
        cls.buyer = User.objects.create_user(username="buyer")
        cls.store = make_store()
        cls.product = make_product(cls.store, name="Test Product", stock=5)
        cls.url = reverse("cart-item-add")

    def setUp(self):
        self.client.force_authenticate(user=self.buyer)

    def _add(self, product_id=None, quantity=1):
        if product_id is None:
            product_id = self.product.id
        return self.client.post(
            self.url,
            data={"product": product_id, "quantity": quantity},
            format="json",
        )

    def test_authenticated_user_can_add_product_to_cart(self):
        self.assertFalse(Cart.objects.filter(user=self.buyer).exists())

        response = self._add(quantity=2)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cart = Cart.objects.get(user=self.buyer)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)

        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(response.data["id"], cart_item.id)
        self.assertEqual(response.data["quantity"], 2)

    def test_add_to_cart_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self._add()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Cart.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_add_inactive_product(self):
        # Safe: self.product is a per-test deep copy, and the test
        # transaction rolls the UPDATE back afterwards.
        self.product.is_active = False
        self.product.save()

        response = self._add()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product", response.data)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_add_nonexistent_product(self):
        response = self._add(product_id=999999)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product", response.data)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_add_zero_or_negative_quantity(self):
        for quantity in (0, -1):
            with self.subTest(quantity=quantity):
                response = self._add(quantity=quantity)

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertIn("quantity", response.data)

        self.assertEqual(CartItem.objects.count(), 0)

    def test_adding_same_product_twice_increments_existing_item(self):
        first_response = self._add(quantity=1)
        second_response = self._add(quantity=1)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)

        cart_item = CartItem.objects.get(
            cart__user=self.buyer, product=self.product
        )

        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(
            first_response.data["id"], second_response.data["id"]
        )
        self.assertEqual(second_response.data["quantity"], 2)

    def test_repeat_add_does_not_exceed_available_stock(self):
        first_response = self._add(quantity=3)
        second_response = self._add(quantity=3)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", second_response.data)

        cart_item = CartItem.objects.get(
            cart__user=self.buyer, product=self.product
        )

        self.assertEqual(cart_item.quantity, 3)
        self.assertLessEqual(cart_item.quantity, self.product.stock)

    def test_cannot_add_more_than_available_stock(self):
        self.assertFalse(Cart.objects.filter(user=self.buyer).exists())

        response = self._add(quantity=6)  # stock is 5

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertFalse(Cart.objects.filter(user=self.buyer).exists())


class CartItemDetailViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Before: this 7-object graph was rebuilt for all 12 tests
        # (~84 INSERTs). Now: 8 INSERTs, once, stable pks included.
        cls.buyer = User.objects.create_user(username="buyer")
        cls.other_user = User.objects.create_user(username="otherbuyer")
        cls.store = make_store()
        cls.product = make_product(cls.store, name="Test Product", stock=5)
        cls.cart = Cart.objects.create(user=cls.buyer)
        cls.cart_item = CartItem.objects.create(
            cart=cls.cart, product=cls.product, quantity=2
        )
        cls.url = reverse(
            "cart-item-detail", kwargs={"pk": cls.cart_item.pk}
        )

    def setUp(self):
        self.client.force_authenticate(user=self.buyer)

    def test_owner_can_retrieve_cart_item(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.cart_item.id)
        self.assertEqual(response.data["quantity"], 2)
        self.assertNotIn("product", response.data)
        self.assertEqual(
            response.data["product_detail"]["id"], self.product.id
        )

    def test_other_user_cannot_retrieve_cart_item(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )

    def test_owner_can_update_cart_item_quantity(self):
        response = self.client.patch(
            self.url, data={"quantity": 4}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 4)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(
            CartItem.objects.get(pk=self.cart_item.pk).quantity, 4
        )

    def test_cannot_update_quantity_above_product_stock(self):
        response = self.client.patch(
            self.url, data={"quantity": 6}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(
            CartItem.objects.get(pk=self.cart_item.pk).quantity, 2
        )

    def test_other_user_cannot_update_cart_item(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            self.url, data={"quantity": 4}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            CartItem.objects.get(pk=self.cart_item.pk).quantity, 2
        )

    def test_cannot_update_cart_item_product(self):
        other_product = make_product(
            self.store, name="Other Product", price="50.00"
        )

        response = self.client.patch(
            self.url, data={"product": other_product.id}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Only the 'quantity' field can be updated.",
        )
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(
            CartItem.objects.get(pk=self.cart_item.pk).product_id,
            self.product.id,
        )

    def test_empty_patch_is_rejected_without_modifying_item(self):
        original_updated_at = self.cart_item.updated_at

        response = self.client.patch(self.url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"quantity": ["This field is required."]}
        )
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)
        self.assertEqual(self.cart_item.updated_at, original_updated_at)

    def test_owner_can_delete_cart_item(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )
        self.assertTrue(Cart.objects.filter(user=self.buyer).exists())
        self.assertTrue(
            Product.objects.filter(pk=self.product.pk).exists()
        )

    def test_other_user_cannot_delete_cart_item(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            CartItem.objects.get(pk=self.cart_item.pk).quantity, 2
        )

    def test_cart_item_detail_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            CartItem.objects.filter(pk=self.cart_item.pk).exists()
        )

    def test_cart_item_response_includes_correct_subtotal(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["subtotal"], "200.00")


class OrderListViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # One shared store chain for the whole class: every test below
        # only writes the products/carts that actually differ.
        cls.user = User.objects.create_user(username="buyer")
        cls.store = make_store()
        cls.url = reverse("order-list")

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    # -- helpers -----------------------------------------------------------

    def _cancel(self, order):
        return self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"status": Order.OrderStatus.CANCELLED},
            format="json",
        )

    def _checkout_pending_order(self, quantity=3, stock=10):
        product = make_product(self.store, stock=stock)
        cart_with_items(self.user, (product, quantity))

        response = self.client.post(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return product, Order.objects.get(user=self.user)

    # -- tests -------------------------------------------------------------

    def test_cannot_checkout_without_a_cart(self):
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

        response = self.client.post(self.url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"detail": "Cannot checkout an empty cart."}
        )
        self.assertFalse(Cart.objects.filter(user=self.user).exists())
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_cannot_checkout_existing_empty_cart(self):
        cart = Cart.objects.create(user=self.user)

        response = self.client.post(self.url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"detail": "Cannot checkout an empty cart."}
        )
        self.assertTrue(
            Cart.objects.filter(pk=cart.pk, user=self.user).exists()
        )
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_checkout_rejects_inactive_product(self):
        product = make_product(
            self.store, name="Inactive Product", is_active=False
        )
        cart_with_items(self.user, (product, 1))

        response = self.client.post(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Inactive Product is no longer available.",
        )
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_insufficient_stock(self):
        product = make_product(self.store, name="Limited Product", stock=2)
        cart_with_items(self.user, (product, 5))

        response = self.client.post(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Not enough stock for Limited Product. Available stock: 2.",
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Product.objects.get(pk=product.pk).stock, 2)
        self.assertEqual(
            CartItem.objects.get(product=product).quantity, 5
        )

    def test_checkout_saves_current_product_price(self):
        product = make_product(self.store, name="Price Snapshot Product")
        cart_with_items(self.user, (product, 2))

        response = self.client.post(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_item = Order.objects.get(user=self.user).order_items.get(
            product=product
        )
        self.assertEqual(order_item.unit_price, Decimal("100.00"))

    def test_successful_checkout_empties_cart(self):
        product = make_product(self.store, name="Cart Product")
        cart = cart_with_items(self.user, (product, 2))

        response = self.client.post(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(cart.cart_items.count(), 0)
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_checkout_creates_order_with_multiple_products(self):
        product_one = make_product(self.store, name="Product One")
        product_two = make_product(
            self.store, name="Product Two", price="200.00", stock=8
        )
        cart_with_items(self.user, (product_one, 2), (product_two, 3))

        response = self.client.post(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.order_items.count(), 2)

        item_one = order.order_items.get(product=product_one)
        item_two = order.order_items.get(product=product_two)

        self.assertEqual(item_one.quantity, 2)
        self.assertEqual(item_one.unit_price, Decimal("100.00"))
        self.assertEqual(item_two.quantity, 3)
        self.assertEqual(item_two.unit_price, Decimal("200.00"))
        self.assertEqual(Product.objects.get(pk=product_one.pk).stock, 8)
        self.assertEqual(Product.objects.get(pk=product_two.pk).stock, 5)

    def test_order_total_price_is_calculated_correctly(self):
        product_one = make_product(self.store, name="Product One")
        product_two = make_product(self.store, name="Product Two", price="200.00")
        cart_with_items(self.user, (product_one, 2), (product_two, 3))

        response = self.client.post(self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Order.objects.get(user=self.user).total_price, Decimal("800.00")
        )

    def test_buyer_can_cancel_pending_order_and_stock_is_restored(self):
        product, order = self._checkout_pending_order(quantity=3, stock=10)

        # 10 - 3 = 7 after checkout.
        self.assertEqual(Product.objects.get(pk=product.pk).stock, 7)

        response = self._cancel(order)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        product.refresh_from_db()

        self.assertEqual(order.status, Order.OrderStatus.CANCELLED)
        # 7 + 3 = 10 after cancellation.
        self.assertEqual(product.stock, 10)

    def test_cancelling_twice_restores_stock_only_once(self):
        product, order = self._checkout_pending_order()

        self.assertEqual(self._cancel(order).status_code, status.HTTP_200_OK)
        self.assertEqual(
            self._cancel(order).status_code, status.HTTP_400_BAD_REQUEST
        )

        product.refresh_from_db()
        self.assertEqual(product.stock, 10)

    def test_non_pending_order_cannot_be_cancelled(self):
        product, order = self._checkout_pending_order()
        Order.objects.filter(pk=order.pk).update(
            status=Order.OrderStatus.SHIPPED
        )

        self.assertEqual(
            self._cancel(order).status_code, status.HTTP_400_BAD_REQUEST
        )

        product.refresh_from_db()
        self.assertEqual(product.stock, 7)

    def test_cannot_cancel_another_users_order(self):
        product, order = self._checkout_pending_order()
        self.client.force_authenticate(
            user=User.objects.create_user(username="other-buyer")
        )

        self.assertEqual(
            self._cancel(order).status_code, status.HTTP_404_NOT_FOUND
        )

        product.refresh_from_db()
        self.assertEqual(product.stock, 7)

    def test_rejects_non_cancel_status(self):
        _, order = self._checkout_pending_order()

        response = self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"status": "shipped"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductWriteTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.seller_user = User.objects.create_user(username="product-seller")
        cls.seller_profile = SellerProfile.objects.create(
            user=cls.seller_user, business_name="Product Seller"
        )
        cls.store = Store.objects.create(
            seller=cls.seller_profile, store_name="Product Store"
        )
        # Shared rival-seller graph for the four permission tests.
        cls.other_store = make_store(
            username="other-seller",
            business_name="Other Seller",
            store_name="Other Store",
        )
        cls.other_user = cls.other_store.seller.user
        # Shared product: deleting/mutating it inside a test is safe --
        # the test transaction rolls everything back.
        cls.product = make_product(cls.store, name="Private Product")
        cls.url = reverse("product-list")

    def setUp(self):
        self.client.force_authenticate(user=self.seller_user)

    def _detail(self, product):
        return reverse("my-product-detail", kwargs={"pk": product.id})

    def test_seller_can_create_product_in_own_store(self):
        payload = {
            "store_id": self.store.id,
            "name": "Test Product",
            "description": "Test description",
            "price": "100.00",
            "stock": 5,
            "is_active": True,
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        product = Product.objects.get(name="Test Product")

        self.assertEqual(product.store, self.store)
        self.assertEqual(product.price, Decimal("100.00"))
        self.assertEqual(product.stock, 5)
        self.assertTrue(product.is_active)

    def test_seller_cannot_create_product_in_another_seller_store(self):
        payload = {
            "store_id": self.other_store.id,
            "name": "Unauthorized Product",
            "description": "Should not be created",
            "price": "100.00",
            "stock": 5,
            "is_active": True,
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            Product.objects.filter(name="Unauthorized Product").exists()
        )

    def test_seller_cannot_access_another_sellers_product(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self._detail(self.product))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_seller_cannot_update_another_sellers_product(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            self._detail(self.product),
            data={"price": "50.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            Product.objects.get(pk=self.product.pk).price, Decimal("100.00")
        )

    def test_seller_cannot_delete_another_sellers_product(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(self._detail(self.product))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Product.objects.filter(pk=self.product.id).exists()
        )

    def test_seller_can_delete_own_product(self):
        response = self.client.delete(self._detail(self.product))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Product.objects.filter(pk=self.product.id).exists()
        )


class StoreWriteTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.seller_user = User.objects.create_user(username="store-seller")
        cls.seller_profile = SellerProfile.objects.create(
            user=cls.seller_user, business_name="Store Seller"
        )
        cls.store = Store.objects.create(
            seller=cls.seller_profile, store_name="My Store"
        )
        cls.other_store = make_store(
            username="other-seller",
            business_name="Other Seller",
            store_name="Other Store",
        )
        cls.url = reverse("store-list")

    def setUp(self):
        self.client.force_authenticate(user=self.seller_user)

    def _detail(self, store):
        return reverse("my-stores-detail", kwargs={"pk": store.id})

    def test_seller_can_create_store(self):
        payload = {
            "store_name": "My New Store",
            "description": "My marketplace store",
            "location": "Lagos",
            "is_active": True,
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(
            Store.objects.get(store_name="My New Store").seller,
            self.seller_profile,
        )

    def test_seller_can_access_own_store(self):
        response = self.client.get(self._detail(self.store))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["store_name"], "My Store")

    def test_seller_cannot_access_another_sellers_store(self):
        response = self.client.get(self._detail(self.other_store))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_seller_cannot_update_another_sellers_store(self):
        response = self.client.patch(
            self._detail(self.other_store),
            data={"store_name": "Hacked Store"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            Store.objects.get(pk=self.other_store.pk).store_name,
            "Other Store",
        )

    def test_seller_cannot_delete_another_sellers_store(self):
        response = self.client.delete(self._detail(self.other_store))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Store.objects.filter(pk=self.other_store.id).exists()
        )

    def test_seller_can_update_own_store(self):
        response = self.client.patch(
            self._detail(self.store),
            data={"store_name": "New Store Name"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Store.objects.get(pk=self.store.pk).store_name, "New Store Name"
        )

    def test_seller_can_delete_own_store(self):
        response = self.client.delete(self._detail(self.store))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Store.objects.filter(pk=self.store.id).exists()
        )


class UserRegistrationTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("user-register")
        # Pre-hash once: this fixture used to cost a PBKDF2 round per test.
        cls.existing = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPassword123",
        )

    def test_user_can_register(self):
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123",
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_password_is_hashed(self):
        payload = {
            "username": "secureuser",
            "email": "secure@example.com",
            "password": "StrongPassword123",
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="secureuser")

        self.assertNotEqual(user.password, "StrongPassword123")
        self.assertTrue(user.check_password("StrongPassword123"))

    def test_duplicate_username_is_rejected(self):
        payload = {
            "username": "existinguser",
            "email": "another@example.com",
            "password": "StrongPassword123",
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            User.objects.filter(username="existinguser").count(), 1
        )


class JWTAuthenticationTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # One hashed password for the class instead of one per test --
        # and with MD5 test settings even this one costs microseconds.
        cls.user = User.objects.create_user(
            username="jwtuser", password="StrongPassword123"
        )
        cls.url = reverse("token-obtain-pair")

    def test_valid_credentials_return_tokens(self):
        response = self.client.post(
            self.url,
            data={"username": "jwtuser", "password": "StrongPassword123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            self.url,
            data={"username": "jwtuser", "password": "WrongPassword123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_requires_authentication(self):
        response = self.client.get(reverse("cart"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_token_can_access_protected_endpoint(self):
        token_response = self.client.post(
            self.url,
            data={"username": "jwtuser", "password": "StrongPassword123"},
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get(reverse("cart"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
