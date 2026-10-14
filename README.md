# Marketplace API

A multi-vendor e-commerce REST API built with **Python, Django, and
Django REST Framework**.

Marketplace API is designed as a backend system where users can shop as
customers, create seller profiles, operate multiple stores, manage
products and inventory, maintain shopping carts, and place orders.

The project focuses not only on CRUD functionality, but also on
practical backend engineering concerns such as **authentication,
resource ownership, relational data modelling, inventory consistency,
transactional checkout, validation, testing, and API documentation**.

> 🚧 **Project Status:** Active development. Seller, store, product,
> category, authentication, and ownership functionality are implemented.
> Cart and order workflows are currently being developed.

------------------------------------------------------------------------

## Core Objectives

The project is being developed to demonstrate practical backend
engineering skills including:

-   RESTful API design
-   Relational database modelling
-   JWT authentication
-   Object-level authorization
-   Multi-vendor marketplace architecture
-   Business-rule validation
-   Inventory management
-   Transaction-safe checkout
-   Automated testing
-   API documentation
-   Production-oriented configuration

## Technology Stack

### Backend

-   Python
-   Django
-   Django REST Framework

### Authentication

-   Simple JWT

### Database

-   SQLite --- current development database
-   PostgreSQL --- planned production database

### Additional Packages

-   django-filter
-   django-phonenumber-field
-   phonenumbers

### Planned Engineering Tooling

-   pytest / Django testing tools
-   OpenAPI / Swagger
-   Docker
-   CI/CD
-   Production deployment

## Marketplace Architecture

The platform supports users acting as customers while optionally
becoming sellers.

``` text
User
│
├── SellerProfile
│   │
│   └── Store
│       │
│       └── Product
│           │
│           └── Category
│
├── Cart
│   │
│   └── CartItem
│       │
│       └── Product
│
└── Order
    │
    └── OrderItem
        │
        └── Product
```

A user can shop as a normal customer while also operating one or more
stores through a seller profile.

## Features

### Authentication

-   User registration
-   JWT authentication
-   Access tokens
-   Refresh tokens
-   Authenticated API operations

Authentication identifies the current user through `JWT → request.user`.
Authorization is applied separately to determine which resources that
user is allowed to manage.

### Seller Profiles

-   Create a seller profile
-   Retrieve seller profiles
-   Retrieve the authenticated seller's profile
-   Update the authenticated seller's profile
-   Delete the authenticated seller's profile
-   Enforce one seller profile per user
-   Frontend-friendly username and business-name representation

### Multi-Store Management

-   Sellers can operate multiple stores
-   Create and browse stores
-   Retrieve stores owned by the authenticated seller
-   Retrieve individual owned stores
-   Update and delete owned stores
-   Prevent sellers from modifying stores they do not own
-   Separate public marketplace and seller-management endpoints

### Product Management

-   Products belong to stores
-   Products can be assigned to categories
-   Sellers can create products only in stores they own
-   Browse marketplace products
-   Retrieve products across all stores owned by a seller
-   Owner-only product updates and deletion
-   Product price and stock validation
-   Active/inactive product status

### Categories

-   Category CRUD operations
-   Unique category names
-   Automatic slug generation
-   Unique slug handling

### Shopping Cart

> 🚧 Currently under development.

Each user has at most one shopping cart.

Planned/current cart capabilities: - Automatic cart creation - Add
products to cart - Update item quantities - Remove cart items - Clear
cart - Validate product availability - Validate requested quantities
against stock - Prevent duplicate product entries - Calculate cart
totals

### Orders & Checkout

> 🚧 Planned / under development.

The checkout system will convert validated cart contents into persistent
orders and is designed to support: - Multi-product orders - Products
from multiple sellers - Price snapshots at purchase time - Inventory
reduction - Order totals - Order status lifecycle - Customer order
history - Seller order visibility - Transaction-safe checkout -
Prevention of inconsistent inventory

## Authorization & Ownership

One of the core design principles of Marketplace API is:

> **Authentication tells the API who the user is. Authorization
> determines what that user is allowed to do.**

Product ownership can be verified through:

``` text
Product → Store → SellerProfile → User
```

This prevents an authenticated seller from modifying another seller's
resources simply by changing an object ID in the URL.

## Server-Controlled Ownership

Sensitive ownership relationships are derived from the authenticated
user rather than trusted directly from client input.

``` text
JWT → request.user → SellerProfile → Store
JWT → request.user → Cart → CartItem
```

## API Structure

### Authentication

``` text
POST /register/
POST /token/
POST /token/refresh/
```

### Seller Profiles

``` text
GET    /seller-profiles/
POST   /seller-profiles/
GET    /seller-profiles/<id>/

GET    /seller-profiles/me/
PATCH  /seller-profiles/me/
PUT    /seller-profiles/me/
DELETE /seller-profiles/me/
```

### Stores

Marketplace:

``` text
GET  /stores/
POST /stores/
GET  /stores/<id>/
```

Seller management:

``` text
GET    /stores/me/
GET    /stores/me/<id>/
PATCH  /stores/me/<id>/
PUT    /stores/me/<id>/
DELETE /stores/me/<id>/
```

### Products

Marketplace:

``` text
GET  /products/
POST /products/
GET  /products/<id>/
```

Seller management:

``` text
GET    /products/me/
GET    /products/me/<id>/
PATCH  /products/me/<id>/
PUT    /products/me/<id>/
DELETE /products/me/<id>/
```

### Categories

``` text
GET    /categories/
POST   /categories/
GET    /categories/<id>/
PATCH  /categories/<id>/
PUT    /categories/<id>/
DELETE /categories/<id>/
```

### Cart

Current:

``` text
GET  /cart/
POST /cart/items/
```

Planned:

``` text
PATCH  /cart/items/<id>/
DELETE /cart/items/<id>/
DELETE /cart/
```

## Data Integrity

The project uses model constraints and application-level validation to
protect data integrity.

Examples include: - One seller profile per user - One cart per user -
Unique product entries within a cart - Positive cart quantities -
Positive product prices - Non-negative inventory - Unique category
names - Unique category slugs - Protected product relationships for
historical order data

## Planned Checkout Safety

Checkout will be treated as a transactional operation rather than a
sequence of unrelated database writes.

``` text
Customer requests checkout
          ↓
Validate cart
          ↓
Validate product availability
          ↓
Validate inventory
          ↓
Begin database transaction
          ↓
Create Order
          ↓
Create OrderItems
          ↓
Capture purchase prices
          ↓
Reduce inventory
          ↓
Clear cart
          ↓
Commit transaction
```

If a critical operation fails, the transaction should roll back rather
than leaving a partially completed order.

## Testing Strategy

Planned automated test areas include:

### Authentication

-   Registration
-   JWT authentication
-   Unauthorized requests

### Permissions

-   Seller can modify own store
-   Seller cannot modify another seller's store
-   Seller can modify own product
-   Seller cannot modify another seller's product

### Cart

-   Add product
-   Prevent invalid quantities
-   Prevent unavailable products
-   Handle duplicate cart items
-   Prevent access to another user's cart

### Checkout

-   Successful checkout
-   Insufficient inventory
-   Product becomes unavailable
-   Correct order totals
-   Correct price snapshots
-   Correct inventory reduction
-   Transaction rollback on failure

## Installation

Clone the repository:

``` bash
git clone <repository-url>
cd MarketplaceAPI
```

Using Pipenv:

``` bash
pipenv install
pipenv shell
```

Apply database migrations:

``` bash
python manage.py migrate
```

Run the development server:

``` bash
python manage.py runserver
```

## Environment Configuration

Production-sensitive configuration will be stored using environment
variables rather than committed directly to source control.

Examples:

``` text
SECRET_KEY
DEBUG
DATABASE_URL
ALLOWED_HOSTS
```

Secrets and local environment files should never be committed to the
repository.

## Roadmap

### Phase 1 --- Marketplace Foundation

-   [x] Django project setup
-   [x] User registration
-   [x] JWT authentication
-   [x] Seller profiles
-   [x] Category management
-   [x] Multi-store architecture
-   [x] Product management
-   [x] Seller ownership authorization

### Phase 2 --- Customer Commerce

-   [x] Cart model
-   [x] Cart item model
-   [x] Authenticated cart creation/retrieval
-   [ ] Cart item stock validation
-   [ ] Duplicate cart-item handling
-   [ ] Cart item quantity updates
-   [ ] Remove cart items
-   [ ] Cart totals

### Phase 3 --- Checkout & Orders

-   [ ] Checkout service
-   [ ] Transaction-safe order creation
-   [ ] Inventory reduction
-   [ ] Price snapshots
-   [ ] Customer order history
-   [ ] Seller order management
-   [ ] Order status workflow

### Phase 4 --- API Quality

-   [ ] Filtering
-   [ ] Searching
-   [ ] Sorting
-   [ ] Pagination
-   [ ] Consistent error responses
-   [ ] API documentation

### Phase 5 --- Engineering & Delivery

-   [ ] PostgreSQL
-   [ ] Comprehensive automated tests
-   [ ] Test coverage reporting
-   [ ] Environment-based configuration
-   [ ] Docker
-   [ ] Continuous integration
-   [ ] Production deployment

## Engineering Questions Addressed by the Project

-   How should ownership be enforced in a multi-vendor marketplace?
-   How can one seller securely operate multiple stores?
-   How should products be associated with stores without trusting
    client-supplied ownership?
-   How should inventory be handled when multiple customers attempt to
    purchase limited stock?
-   How should historical orders preserve product prices after sellers
    change their current prices?
-   How can checkout avoid partially created orders?
-   How should public marketplace endpoints differ from
    seller-management endpoints?
-   How should API representations remain frontend-friendly without
    compromising normalized database relationships?

## Current Status

Marketplace API is an **active backend engineering project**.

The marketplace foundation --- authentication, sellers, stores,
products, categories, and ownership authorization --- is operational.

Current development is focused on the customer shopping-cart workflow.
The next major milestone is transactional checkout and order processing,
followed by testing, PostgreSQL migration, documentation,
containerization, and deployment.

## Author

**Akanbi Boluwatife Emmanuel**

Backend Developer --- Python / Django REST Framework
