# Hackathon Challenge Areas

This document provides a detailed technical breakdown of each challenge area for the **Build Beyond Limits** hackathon. Each section describes the subsystem, the Valkey data structures and modules to use, expected API contracts, and implementation guidance.

Use the [valkey-bundle](https://github.com/valkey-io/valkey-bundle) Docker image which includes all modules (Search, JSON, Bloom, etc.):

```bash
docker run -d --name valkey -p 6379:6379 valkey/valkey-bundle:9-alpine
```

---

## ID Strategy

All entity IDs use **UUIDv7** (RFC 9562) with a **domain prefix** in the format `domain:uuidv7`. UUIDv7 embeds a Unix timestamp in the most significant bits, which provides:

- **Monotonic ordering**: IDs are naturally sortable by creation time without a separate `createdAt` index.
- **K-sortable**: Valkey Sorted Sets with UUIDv7 as members are inherently time-ordered.
- **No coordination**: Generate IDs client-side without a central sequence.
- **Indexing efficiency**: Lexicographic sorting of UUIDv7 strings matches chronological order, making `ZRANGEBYLEX` and prefix scans efficient.
- **Self-describing**: The domain prefix makes IDs unambiguous — you always know what entity type an ID refers to without additional context.

### Format

```
{domain}:{uuidv7}
```

| Domain | Entity | Example |
|--------|--------|---------|
| `user` | User account | `user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e` |
| `product` | Product | `product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f` |
| `category` | Category | `category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b` |
| `vendor` | Vendor/Seller | `vendor:0192d4e7-4d5e-7b7c-9e9f-1a2b3c4d5e6f` |
| `order` | Order | `order:0192d4e8-5e6f-7c8d-8a0b-2c3d4e5f6a7b` |
| `addr` | Address | `addr:0192d4e1-a2c8-7d4b-8f3e-1a9b5c7d2e4f` |
| `ad` | Advertisement | `ad:0192d4e9-6f7a-7d8e-9b0c-3d4e5f6a7b8c` |
| `session` | Auth session | `session:0192d4f0-1a2b-7c3d-8e4f-5a6b7c8d9e0f` |

### Example generation (Node.js):
```js
import { v7 as uuidv7 } from 'uuid'; // npm install uuid@^9

function createId(domain) {
  return `${domain}:${uuidv7()}`;
}

const userId = createId('user');       // "user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e"
const productId = createId('product'); // "product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f"
const orderId = createId('order');     // "order:0192d4e8-5e6f-7c8d-8a0b-2c3d4e5f6a7b"
```

### Parsing
```js
function parseId(id) {
  const colonIndex = id.indexOf(':');
  const domain = id.substring(0, colonIndex);
  const uuid = id.substring(colonIndex + 1);
  return { domain, uuid };
}

const { domain, uuid } = parseId('user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e');
// domain = "user", uuid = "0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e"
```

---

## Sample Data Contracts

The following JSON structures define the shared data contracts all teams should follow. This ensures frontend and backend teams can work in parallel with consistent schemas.

All `id` fields follow the `domain:uuidv7` format. The monotonic property of UUIDv7 means you can sort entities by ID to get chronological order — no need for a separate timestamp index in most cases. The domain prefix makes every ID self-describing.

### Users

```json
{
  "id": "user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e",
  "email": "priya.sharma@example.com",
  "passwordHash": "$2b$12$LJ3m4x...",
  "firstName": "Priya",
  "lastName": "Sharma",
  "phone": "+91-9876543210",
  "avatar": "/assets/avatars/priya.jpg",
  "role": "customer",
  "addresses": [
    {
      "id": "addr:0192d4e1-a2c8-7d4b-8f3e-1a9b5c7d2e4f",
      "label": "Home",
      "street": "42 MG Road, Banjara Hills",
      "city": "Hyderabad",
      "state": "Telangana",
      "postalCode": "500034",
      "country": "IN",
      "lat": 17.4156,
      "lng": 78.4347,
      "isDefault": true
    }
  ],
  "preferences": {
    "currency": "INR",
    "language": "en",
    "notifications": true
  },
  "createdAt": "2025-01-15T10:30:00Z",
  "lastLoginAt": "2025-05-20T14:22:00Z"
}
```

### Categories

```json
[
  {
    "id": "category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b",
    "name": "Electronics",
    "slug": "electronics",
    "icon": "desktop",
    "parentId": null,
    "children": ["category:0192d4e2-3a7b-7e1f-8c4d-2b6a9f0e5d7c", "category:0192d4e2-4c8d-7a2e-9f1b-3d5c7e8a0b4f", "category:0192d4e2-5d9e-7b3f-8a2c-4e6d1f9b0c5a", "category:0192d4e2-6eaf-7c4a-9b3d-5f7e2a0c1d6b"]
  },
  {
    "id": "category:0192d4e2-3a7b-7e1f-8c4d-2b6a9f0e5d7c",
    "name": "Smartphones",
    "slug": "smartphones",
    "icon": "device-mobile",
    "parentId": "category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b",
    "children": []
  },
  {
    "id": "category:0192d4e3-7b1c-7d4e-8a2f-9c3b5d6e0f1a",
    "name": "Fashion",
    "slug": "fashion",
    "icon": "t-shirt",
    "parentId": null,
    "children": ["category:0192d4e3-8c2d-7e5f-9b3a-0d4c6e7f1a2b", "category:0192d4e3-9d3e-7f6a-8c4b-1e5d7f0a2b3c", "category:0192d4e3-ae4f-7a7b-9d5c-2f6e8a1b3c4d"]
  },
  {
    "id": "category:0192d4e4-1a2b-7c3d-8e4f-5a6b7c8d9e0f",
    "name": "Home & Kitchen",
    "slug": "home-kitchen",
    "icon": "house",
    "parentId": null,
    "children": ["category:0192d4e4-2b3c-7d4e-9f5a-6b7c8d9e0f1a", "category:0192d4e4-3c4d-7e5f-8a6b-7c8d9e0f1a2b", "category:0192d4e4-4d5e-7f6a-9b7c-8d9e0f1a2b3c"]
  },
  {
    "id": "category:0192d4e5-5e6f-7a7b-8c8d-9e0f1a2b3c4d",
    "name": "Sports & Outdoors",
    "slug": "sports-outdoors",
    "icon": "basketball",
    "parentId": null,
    "children": ["category:0192d4e5-6f7a-7b8c-9d9e-0f1a2b3c4d5e", "category:0192d4e5-7a8b-7c9d-8e0f-1a2b3c4d5e6f", "category:0192d4e5-8b9c-7d0e-9f1a-2b3c4d5e6f7a"]
  }
]
```

### Products

```json
{
  "id": "product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f",
  "sku": "ELEC-PHN-SAM-001",
  "name": "Galaxy Ultra Pro 256GB",
  "slug": "galaxy-ultra-pro-256gb",
  "description": "Flagship smartphone with 200MP camera, 6.8\" AMOLED display, and 5000mAh battery.",
  "shortDescription": "200MP camera, 6.8\" AMOLED, 5000mAh",
  "categoryId": "category:0192d4e2-3a7b-7e1f-8c4d-2b6a9f0e5d7c",
  "vendorId": "vendor:0192d4e7-4d5e-7b7c-9e9f-1a2b3c4d5e6f",
  "brand": "Samsung",
  "price": {
    "amount": 89999,
    "currency": "INR",
    "compareAt": 99999
  },
  "images": [
    {
      "url": "/assets/products/galaxy-ultra-front.jpg",
      "alt": "Galaxy Ultra Pro front view",
      "isPrimary": true
    },
    {
      "url": "/assets/products/galaxy-ultra-back.jpg",
      "alt": "Galaxy Ultra Pro back view",
      "isPrimary": false
    }
  ],
  "attributes": {
    "color": "Phantom Black",
    "storage": "256GB",
    "ram": "12GB",
    "display": "6.8 inch AMOLED",
    "battery": "5000mAh",
    "os": "Android 15"
  },
  "tags": ["smartphone", "5g", "flagship", "camera", "samsung"],
  "inventory": {
    "quantity": 150,
    "reserved": 12,
    "warehouse": "HYD-WH-01"
  },
  "ratings": {
    "average": 4.6,
    "count": 2341
  },
  "embedding": [0.023, -0.156, 0.891, 0.445, ...],
  "status": "active",
  "createdAt": "2025-03-01T08:00:00Z",
  "updatedAt": "2025-05-18T12:30:00Z"
}
```

### Vendors

```json
{
  "id": "vendor:0192d4e7-4d5e-7b7c-9e9f-1a2b3c4d5e6f",
  "name": "TechWorld Electronics",
  "slug": "techworld-electronics",
  "email": "support@techworld.in",
  "phone": "+91-4012345678",
  "logo": "/assets/vendors/techworld-logo.png",
  "rating": 4.7,
  "totalProducts": 342,
  "totalSales": 15420,
  "address": {
    "street": "Plot 15, HITEC City",
    "city": "Hyderabad",
    "state": "Telangana",
    "postalCode": "500081",
    "country": "IN",
    "lat": 17.4435,
    "lng": 78.3772
  },
  "verified": true,
  "joinedAt": "2024-06-15T00:00:00Z"
}
```

### Orders

```json
{
  "id": "order:0192d4e8-5e6f-7c8d-8a0b-2c3d4e5f6a7b",
  "userId": "user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e",
  "status": "confirmed",
  "items": [
    {
      "productId": "product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f",
      "sku": "ELEC-PHN-SAM-001",
      "name": "Galaxy Ultra Pro 256GB",
      "quantity": 1,
      "price": 89999,
      "vendorId": "vendor:0192d4e7-4d5e-7b7c-9e9f-1a2b3c4d5e6f"
    }
  ],
  "subtotal": 89999,
  "discount": 5000,
  "couponCode": "VALKEY10",
  "tax": 15300,
  "shipping": 0,
  "total": 100299,
  "shippingAddress": {
    "street": "42 MG Road, Banjara Hills",
    "city": "Hyderabad",
    "state": "Telangana",
    "postalCode": "500034",
    "country": "IN",
    "lat": 17.4156,
    "lng": 78.4347
  },
  "payment": {
    "method": "upi",
    "transactionId": "txn_abc123",
    "status": "captured"
  },
  "delivery": {
    "estimatedAt": "2025-05-25T18:00:00Z",
    "trackingId": "DEL-HYD-98765",
    "currentLat": 17.4300,
    "currentLng": 78.4100,
    "status": "in_transit"
  },
  "createdAt": "2025-05-22T09:15:00Z",
  "updatedAt": "2025-05-22T10:00:00Z"
}
```

---

## Challenge 1: User Authentication

### Objective
Implement user registration, login, and session management using Valkey as the session store.

### Technical Requirements

- **Registration**: Hash passwords with bcrypt (cost factor 12+), store user JSON in Valkey using `JSON.SET`.
- **Login**: Validate credentials, generate a session token (UUID v4 or JWT), store it in Valkey with a TTL.
- **Session Management**: Use Valkey strings with expiration for session tokens. Refresh TTL on each authenticated request.
- **Logout**: Delete the session key from Valkey.

### Valkey Commands & Data Structures

```
# Store user profile (key = userId, e.g. "user:0192d4e0-...")
JSON.SET {userId} $ '{...user JSON...}'

# Create session (expires in 24 hours)
SET session:{token} {userId} EX 86400

# Validate session
GET session:{token}

# Refresh session TTL
EXPIRE session:{token} 86400

# Logout
DEL session:{token}

# Track failed login attempts (rate limiting)
INCR login_attempts:{email}
EXPIRE login_attempts:{email} 900
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create new user account |
| POST | `/api/auth/login` | Authenticate and return session token |
| POST | `/api/auth/logout` | Invalidate session |
| GET | `/api/auth/me` | Get current user from session |
| POST | `/api/auth/refresh` | Refresh session TTL |

### Acceptance Criteria
- Passwords are never stored in plaintext
- Sessions expire after 24 hours of inactivity
- Failed login attempts are rate-limited (max 5 per 15 minutes)
- Concurrent sessions per user are tracked

---

## Challenge 2: Product Catalog

### Objective
Build a product catalog service that stores and retrieves products, categories, and vendor information using Valkey JSON.

### Technical Requirements

- **Product Storage**: Store each product as a JSON document using `JSON.SET`. Support partial updates with `JSON.SET` on nested paths.
- **Category Hierarchy**: Model parent-child category relationships. Support breadcrumb navigation.
- **Filtering**: Filter products by category, price range, brand, attributes, and vendor.
- **Pagination**: Implement cursor-based or offset pagination for product listings.

### Valkey Commands & Data Structures

```
# Store product (key = productId, e.g. "product:0192d4e6-...")
JSON.SET {productId} $ '{...product JSON...}'

# Get product
JSON.GET {productId}

# Get specific fields
JSON.GET {productId} $.name $.price $.ratings

# Update inventory
JSON.SET {productId} $.inventory.quantity 138

# Store category (key = categoryId, e.g. "category:0192d4e2-...")
JSON.SET {categoryId} $ '{...category JSON...}'

# Category-to-products index (sorted by creation date)
ZADD category_products:{categoryId} {timestamp} {productId}

# Get products in category (paginated, newest first)
ZREVRANGEBYSCORE category_products:{categoryId} +inf -inf LIMIT 0 20

# Brand index
SADD brand_products:{brand} {productId}

# Price range index (score = price in paise)
ZADD price_index 8999900 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f
ZRANGEBYSCORE price_index 5000000 10000000
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/products` | List products (with filters, pagination) |
| GET | `/api/products/:id` | Get single product |
| GET | `/api/categories` | List all categories (tree) |
| GET | `/api/categories/:id/products` | Products in category |
| GET | `/api/vendors/:id/products` | Products by vendor |
| POST | `/api/products` | Create product (vendor/admin) |
| PATCH | `/api/products/:id` | Update product fields |

### Acceptance Criteria
- Products are stored as JSON documents with all fields from the contract
- Category tree supports 2+ levels of nesting
- Filtering by price range, brand, and category works correctly
- Pagination returns consistent results

---

## Challenge 3: Shopping Cart with Coupons

### Objective
Implement a persistent shopping cart with coupon/discount code support using Valkey Hashes and JSON.

### Technical Requirements

- **Cart Storage**: Each user has a cart stored as a Valkey Hash where field = productId and value = quantity, or as a JSON document for richer data.
- **Cart Operations**: Add item, remove item, update quantity, clear cart.
- **Coupon System**: Store coupon definitions with rules (percentage off, fixed amount, minimum order, expiry date, usage limits).
- **Coupon Validation**: Check expiry, minimum order value, usage count, and applicable categories.
- **Guest Carts**: Support anonymous carts tied to a session ID, merged on login.

### Valkey Commands & Data Structures

```
# Cart as Hash (simple: productId -> quantity)
HSET cart:{userId} product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f 2
HSET cart:{userId} product:0192d4e6-3d5f-7b8c-9e0a-1b2c3d4e5f6a 1

# Get full cart
HGETALL cart:{userId}

# Update quantity
HSET cart:{userId} product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f 3

# Remove item
HDEL cart:{userId} product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f

# Clear cart
DEL cart:{userId}

# Cart expiry (abandon after 7 days)
EXPIRE cart:{userId} 604800

# Coupon definition
JSON.SET coupon:{code} $ '{
  "code": "VALKEY10",
  "type": "percentage",
  "value": 10,
  "minOrderAmount": 50000,
  "maxDiscount": 10000,
  "validFrom": "2025-05-01T00:00:00Z",
  "validUntil": "2025-06-30T23:59:59Z",
  "usageLimit": 1000,
  "usedCount": 342,
  "applicableCategories": ["category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b", "category:0192d4e3-7b1c-7d4e-8a2f-9c3b5d6e0f1a"],
  "active": true
}'

# Track coupon usage per user
SADD coupon_used:{code} {userId}
SISMEMBER coupon_used:{code} {userId}

# Increment global usage
JSON.NUMINCRBY coupon:{code} $.usedCount 1
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cart` | Get current user's cart |
| POST | `/api/cart/items` | Add item to cart |
| PATCH | `/api/cart/items/:productId` | Update item quantity |
| DELETE | `/api/cart/items/:productId` | Remove item from cart |
| DELETE | `/api/cart` | Clear entire cart |
| POST | `/api/cart/coupon` | Apply coupon code |
| DELETE | `/api/cart/coupon` | Remove applied coupon |

### Acceptance Criteria
- Cart persists across browser sessions for logged-in users
- Guest carts merge into user cart on login
- Coupons validate all rules before applying
- A user cannot use the same coupon twice
- Cart shows real-time price calculations with discount

---

## Challenge 4: Trending Products

### Objective
Track product views, purchases, and interactions in real-time to surface trending products using Valkey Sorted Sets.

### Technical Requirements

- **Event Tracking**: Record product views, add-to-cart events, and purchases with timestamps.
- **Trending Score**: Calculate a weighted score: `views * 1 + addToCart * 3 + purchases * 5`.
- **Time Decay**: Trending scores should decay over time. Use sliding windows (last 1 hour, 6 hours, 24 hours).
- **Category Trending**: Track trending per category in addition to global trending.

### Valkey Commands & Data Structures

```
# Increment product score on view
ZINCRBY trending:global:1h 1 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f
ZINCRBY trending:global:24h 1 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f

# Increment on add-to-cart
ZINCRBY trending:global:1h 3 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f
ZINCRBY trending:global:24h 3 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f

# Increment on purchase
ZINCRBY trending:global:1h 5 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f
ZINCRBY trending:global:24h 5 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f

# Category-specific trending
ZINCRBY trending:category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b:1h 1 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f

# Get top 10 trending products
ZREVRANGE trending:global:1h 0 9 WITHSCORES

# Time-series for granular analytics (Sorted Set: score = timestamp, member = productId)
ZADD product_views:{date} {timestamp} {productId}
# Count views in last hour
ZCOUNT product_views:{date} {timestamp - 3600} {timestamp}

# Expire hourly buckets (auto-cleanup)
EXPIRE trending:global:1h 3600
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/trending` | Get global trending products |
| GET | `/api/trending/:categoryId` | Trending in category |
| POST | `/api/events/view` | Record product view |
| POST | `/api/events/add-to-cart` | Record add-to-cart |
| POST | `/api/events/purchase` | Record purchase event |

### Acceptance Criteria
- Trending list updates in real-time as events come in
- Different time windows return different results
- Scores reflect weighted interactions (purchase > add-to-cart > view)
- Stale products naturally fall off trending lists

---

## Challenge 5: Ads

### Objective
Build an ad placement and targeting system that serves relevant ads based on user context (current category, search query, browsing history) using Valkey.

### Technical Requirements

- **Ad Storage**: Store ad creatives with targeting rules (categories, keywords, user segments).
- **Ad Selection**: Given a context (page, category, search term), select the most relevant ad with highest bid.
- **Impression Tracking**: Count impressions and clicks per ad. Enforce daily budget limits.
- **Frequency Capping**: Limit how many times a user sees the same ad per session/day.

### Valkey Commands & Data Structures

```
# Store ad creative (key = adId, e.g. "ad:0192d4e9-...")
JSON.SET {adId} $ '{
  "id": "ad:0192d4e9-6f7a-7d8e-9b0c-3d4e5f6a7b8c",
  "vendorId": "vendor:0192d4e7-4d5e-7b7c-9e9f-1a2b3c4d5e6f",
  "title": "Summer Electronics Sale",
  "imageUrl": "/assets/ads/summer-sale.jpg",
  "targetUrl": "/shop?sale=summer",
  "targetCategories": ["category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b", "category:0192d4e2-3a7b-7e1f-8c4d-2b6a9f0e5d7c"],
  "targetKeywords": ["phone", "laptop", "gadget"],
  "bidAmount": 500,
  "dailyBudget": 50000,
  "status": "active"
}'

# Index ads by category (sorted by bid)
ZADD ads:category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b 500 ad:0192d4e9-6f7a-7d8e-9b0c-3d4e5f6a7b8c

# Track impressions today
INCR ad_impressions:{adId}:{date}
EXPIRE ad_impressions:{adId}:{date} 86400

# Track clicks
INCR ad_clicks:{adId}:{date}

# Frequency cap per user per day
INCR ad_freq:{userId}:{adId}:{date}
EXPIRE ad_freq:{userId}:{adId}:{date} 86400

# Daily spend tracking
INCRBY ad_spend:{adId}:{date} {bidAmount}
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ads?context=category&value=category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b` | Get relevant ads |
| POST | `/api/ads/:adId/impression` | Record impression |
| POST | `/api/ads/:adId/click` | Record click |
| POST | `/api/ads` | Create ad (vendor) |
| GET | `/api/ads/:adId/stats` | Get ad performance |

### Acceptance Criteria
- Ads are served based on relevance to current page context
- Higher bids get priority placement
- Ads stop serving when daily budget is exhausted
- Users don't see the same ad more than 3 times per session
- Click-through rate (CTR) is trackable

---

## Challenge 6: Full-Text Search

### Objective
Implement product search with full-text capabilities using Valkey Search module. Support autocomplete, typo tolerance, and faceted filtering.

### Technical Requirements

- **Index Creation**: Create a search index on product JSON documents covering name, description, brand, tags, category, and price.
- **Query Support**: Full-text queries with stemming, prefix matching, and fuzzy matching.
- **Faceted Search**: Return aggregated counts by category, brand, and price range alongside results.
- **Autocomplete**: Provide search suggestions as the user types (prefix-based).
- **Sorting**: Support sorting by relevance, price (asc/desc), rating, and newest.

### Valkey Commands & Data Structures

```
# Create search index on JSON documents
FT.CREATE idx:products ON JSON PREFIX 1 product:
  SCHEMA
    $.name AS name TEXT WEIGHT 5.0
    $.description AS description TEXT WEIGHT 1.0
    $.brand AS brand TEXT WEIGHT 3.0 SORTABLE
    $.tags AS tags TAG SEPARATOR ","
    $.categoryId AS categoryId TAG
    $.price.amount AS price NUMERIC SORTABLE
    $.ratings.average AS rating NUMERIC SORTABLE
    $.status AS status TAG
    $.createdAt AS createdAt TEXT SORTABLE

# Full-text search
FT.SEARCH idx:products "galaxy phone" LIMIT 0 20

# Search with filters
FT.SEARCH idx:products "@name:galaxy @categoryId:{0192d4e2-3a7b-7e1f-8c4d-2b6a9f0e5d7c} @price:[50000 100000]"
  SORTBY price ASC
  LIMIT 0 20

# Fuzzy search (typo tolerance)
FT.SEARCH idx:products "%%galxy%%" LIMIT 0 10

# Faceted aggregation (count by brand)
FT.AGGREGATE idx:products "phone"
  GROUPBY 1 @brand
  REDUCE COUNT 0 AS count
  SORTBY 2 @count DESC

# Autocomplete suggestions
FT.SUGADD autocomplete "Galaxy Ultra Pro" 100
FT.SUGADD autocomplete "Gaming Laptop" 85
FT.SUGGET autocomplete "gal" FUZZY MAX 5
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search?q=galaxy&category=category:0192d4e2-3a7b-7e1f-8c4d-2b6a9f0e5d7c&minPrice=50000&maxPrice=100000&sort=price_asc&page=1` | Search products |
| GET | `/api/search/suggest?q=gal` | Autocomplete suggestions |
| GET | `/api/search/facets?q=phone` | Get facet counts |

### Response Format

```json
{
  "query": "galaxy phone",
  "total": 47,
  "page": 1,
  "pageSize": 20,
  "results": [
    { "id": "product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f", "name": "Galaxy Ultra Pro 256GB", "score": 0.95, "...": "..." }
  ],
  "facets": {
    "brands": [{ "name": "Samsung", "count": 23 }, { "name": "Apple", "count": 12 }],
    "priceRanges": [{ "range": "50000-100000", "count": 18 }],
    "categories": [{ "id": "category:0192d4e2-3a7b-7e1f-8c4d-2b6a9f0e5d7c", "name": "Smartphones", "count": 35 }]
  }
}
```

### Acceptance Criteria
- Search returns relevant results within 50ms
- Typos in queries still return useful results
- Facets accurately reflect the filtered result set
- Autocomplete responds within 20ms
- Results can be sorted by multiple criteria

---

## Challenge 7: Vector Similarity Search

### Objective
Implement semantic product search using vector embeddings stored in Valkey. Users can search by meaning rather than exact keywords (e.g., "something to keep my coffee warm" → finds thermoses and insulated mugs).

### Technical Requirements

- **Embedding Generation**: Generate vector embeddings for product descriptions using a pre-trained model (e.g., sentence-transformers, OpenAI embeddings). Store as FLOAT32 vectors.
- **Vector Index**: Create a vector similarity index using HNSW or FLAT algorithm.
- **Hybrid Search**: Combine vector similarity with traditional filters (category, price range).
- **Similar Products**: Given a product, find visually or semantically similar products.

### Valkey Commands & Data Structures

```
# Create vector index on product embeddings
FT.CREATE idx:product_vectors ON JSON PREFIX 1 product:
  SCHEMA
    $.name AS name TEXT
    $.categoryId AS categoryId TAG
    $.price.amount AS price NUMERIC
    $.embedding AS embedding VECTOR HNSW 6
      TYPE FLOAT32
      DIM 384
      DISTANCE_METRIC COSINE

# KNN search (find 10 most similar products to query vector)
FT.SEARCH idx:product_vectors
  "*=>[KNN 10 @embedding $query_vec AS score]"
  PARAMS 2 query_vec "\x00\x00..."
  SORTBY score
  RETURN 4 name score price categoryId
  DIALECT 2

# Hybrid: vector search + category filter
FT.SEARCH idx:product_vectors
  "(@categoryId:{0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b})=>[KNN 10 @embedding $query_vec AS score]"
  PARAMS 2 query_vec "\x00\x00..."
  SORTBY score
  DIALECT 2

# Similar products (use product's own embedding as query)
# 1. Get the product embedding
JSON.GET product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f $.embedding
# 2. Use it as query vector in KNN search
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search/semantic?q=keep coffee warm` | Semantic search |
| GET | `/api/products/:id/similar` | Find similar products |
| POST | `/api/search/by-image` | Search by image embedding |

### Acceptance Criteria
- Semantic queries return contextually relevant results even without keyword matches
- Vector search completes within 100ms for 10K+ products
- Similar products endpoint returns genuinely related items
- Hybrid search correctly applies filters on top of vector results

---

## Challenge 8: Analytics with Prometheus

### Objective
Instrument the application with metrics and expose them in Prometheus format. Track business KPIs and system performance using Valkey core data structures for real-time dashboards.

### Technical Requirements

- **Business Metrics**: Track orders per minute, revenue per hour, active users, cart abandonment rate.
- **System Metrics**: Track API response times, Valkey command latency, error rates.
- **Metrics Storage**: Use Valkey Sorted Sets (score = timestamp), Hashes, and HyperLogLog for metrics aggregation.
- **Prometheus Endpoint**: Expose `/metrics` in Prometheus exposition format.
- **Time Bucketing**: Use time-bucketed keys (per minute, per hour) with TTL for automatic cleanup.

### Valkey Commands & Data Structures

```
# Orders counter (per-minute bucket, auto-expires)
INCR metrics:orders:count:{minute_timestamp}
EXPIRE metrics:orders:count:{minute_timestamp} 86400

# Revenue tracking (per-hour bucket)
INCRBY metrics:revenue:{hour_timestamp} 100299
EXPIRE metrics:revenue:{hour_timestamp} 604800

# API latency tracking (Sorted Set: score = latency, member = requestId)
ZADD metrics:api_latency:{minute_timestamp} 45 {requestId}
EXPIRE metrics:api_latency:{minute_timestamp} 3600

# Calculate percentiles from sorted set
ZCARD metrics:api_latency:{minute_timestamp}                    # total count
ZRANGEBYSCORE metrics:api_latency:{minute_timestamp} -inf +inf  # all values sorted
# p50 = element at index count/2, p95 = element at index count*0.95

# Active users (HyperLogLog for unique count)
PFADD active_users:{date}:{hour} {userId}
PFCOUNT active_users:{date}:{hour}

# Gauge-style metrics (current value in a Hash)
HSET metrics:gauges cart_abandonment_rate 0.23
HSET metrics:gauges active_sessions 1542
HSET metrics:gauges items_in_stock 48230

# Counter-style metrics (atomic increment)
INCR metrics:counters:http_requests:{status_code}:{minute_timestamp}
INCR metrics:counters:valkey_commands:{minute_timestamp}
INCR metrics:counters:errors:{service}:{minute_timestamp}

# Query metrics for a time range (scan matching keys)
# Application code iterates over minute buckets between from/to timestamps
# e.g., GET metrics:orders:count:1716372600, GET metrics:orders:count:1716372660, ...

# Histogram buckets for latency distribution
HINCRBY metrics:latency_histogram:{minute_timestamp} "le_10" 1   # <= 10ms
HINCRBY metrics:latency_histogram:{minute_timestamp} "le_50" 1   # <= 50ms
HINCRBY metrics:latency_histogram:{minute_timestamp} "le_100" 1  # <= 100ms
HINCRBY metrics:latency_histogram:{minute_timestamp} "le_500" 1  # <= 500ms
HINCRBY metrics:latency_histogram:{minute_timestamp} "le_inf" 1  # <= +Inf
EXPIRE metrics:latency_histogram:{minute_timestamp} 86400
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Prometheus exposition format |
| GET | `/api/analytics/dashboard` | Real-time dashboard data |
| GET | `/api/analytics/revenue?from=&to=&interval=1h` | Revenue over time |
| GET | `/api/analytics/orders?from=&to=` | Order count over time |
| GET | `/api/analytics/active-users` | Unique active users |

### Prometheus Exposition Format Example

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1542
http_requests_total{method="POST",status="201"} 312

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.01"} 800
http_request_duration_seconds_bucket{le="0.05"} 1200
http_request_duration_seconds_bucket{le="0.1"} 1400
http_request_duration_seconds_bucket{le="0.5"} 1520
http_request_duration_seconds_bucket{le="+Inf"} 1542

# HELP active_users_total Current unique active users
# TYPE active_users_total gauge
active_users_total 1542
```

### Acceptance Criteria
- Prometheus can scrape the `/metrics` endpoint successfully
- Metrics are bucketed by time with automatic TTL-based cleanup
- Dashboard shows real-time updates (< 5 second delay)
- At least 5 business metrics and 3 system metrics are tracked
- Latency percentiles (p50, p95, p99) are calculable from stored data

---

## Challenge 9: Observability with OpenSearch

### Objective
Implement structured logging, distributed tracing, and error tracking. Forward logs to OpenSearch for centralized search and visualization.

### Technical Requirements

- **Structured Logging**: All logs in JSON format with correlation IDs, timestamps, severity levels, and context.
- **Request Tracing**: Assign a trace ID to each incoming request. Propagate through all internal calls.
- **Error Tracking**: Capture and aggregate errors with stack traces, frequency, and affected users.
- **Log Buffering**: Use Valkey Streams as a buffer before forwarding to OpenSearch (prevents log loss during OpenSearch downtime).

### Valkey Commands & Data Structures

```
# Buffer logs in a Valkey Stream
XADD logs:app * level "error" service "cart-service" traceId "trc_abc123"
  message "Failed to apply coupon" userId "user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e"
  timestamp "2025-05-22T09:15:00Z" stack "Error: Invalid coupon..."

# Read logs (consumer group for reliable processing)
XGROUP CREATE logs:app log-forwarder $ MKSTREAM
XREADGROUP GROUP log-forwarder worker-1 COUNT 100 BLOCK 5000 STREAMS logs:app >

# Acknowledge processed logs
XACK logs:app log-forwarder {messageId}

# Trim old logs (keep last 100K entries)
XTRIM logs:app MAXLEN ~ 100000

# Error aggregation
ZINCRBY errors:24h 1 "cart-service:InvalidCoupon"
EXPIRE errors:24h 86400

# Request tracing (store span data)
JSON.SET trace:{traceId} $ '{
  "traceId": "trc_abc123",
  "spans": [
    {"service": "api-gateway", "operation": "POST /cart/coupon", "duration": 45},
    {"service": "cart-service", "operation": "validateCoupon", "duration": 12},
    {"service": "valkey", "operation": "JSON.GET coupon:VALKEY10", "duration": 2}
  ],
  "totalDuration": 45,
  "status": "error"
}'
EXPIRE trace:{traceId} 3600
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/observability/logs?level=error&service=cart-service&limit=50` | Query recent logs |
| GET | `/api/observability/traces/:traceId` | Get full trace |
| GET | `/api/observability/errors` | Top errors (last 24h) |
| GET | `/api/observability/health` | Service health status |

### Acceptance Criteria
- All API requests have a unique trace ID in response headers (`X-Trace-Id`)
- Logs are buffered in Valkey Streams and forwarded to OpenSearch
- No logs are lost during brief OpenSearch outages
- Errors are aggregated and ranked by frequency
- Trace data shows the full request lifecycle across services

---

## Challenge 10: Checkout with Inventory Tracking

### Objective
Implement a checkout flow with atomic inventory reservation, payment processing, and order creation. Prevent overselling using Valkey transactions.

### Technical Requirements

- **Inventory Reservation**: When a user starts checkout, reserve inventory atomically. Release if checkout is abandoned (TTL-based).
- **Atomic Decrement**: Use Lua scripts or transactions to ensure inventory never goes negative.
- **Order Creation**: Create order document on successful payment. Update inventory permanently.
- **Idempotency**: Prevent duplicate orders from double-clicks or retries using idempotency keys.

### Valkey Commands & Data Structures

```
# Atomic inventory check-and-reserve (Lua script)
# KEYS[1] = product inventory key, ARGV[1] = quantity
EVAL "
  local current = tonumber(redis.call('JSON.GET', KEYS[1], '$.inventory.quantity'))
  local reserved = tonumber(redis.call('JSON.GET', KEYS[1], '$.inventory.reserved'))
  local available = current - reserved
  if available >= tonumber(ARGV[1]) then
    redis.call('JSON.NUMINCRBY', KEYS[1], '$.inventory.reserved', ARGV[1])
    return 1
  end
  return 0
" 1 product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f 2

# Reservation with TTL (auto-release after 10 minutes)
SET reservation:{orderId}:{productId} {quantity} EX 600

# On successful payment: commit inventory
JSON.NUMINCRBY {productId} $.inventory.quantity -{quantity}
JSON.NUMINCRBY {productId} $.inventory.reserved -{quantity}
DEL reservation:{orderId}:{productId}

# On abandoned checkout: release reservation
# (handled by TTL expiry + keyspace notification)

# Idempotency key
SET idempotency:{key} {orderId} NX EX 86400

# Store order
JSON.SET {orderId} $ '{...order JSON...}'

# Order history index
ZADD user_orders:{userId} {timestamp} {orderId}
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/checkout/start` | Reserve inventory, create pending order |
| POST | `/api/checkout/payment` | Process payment |
| POST | `/api/checkout/confirm` | Confirm order after payment |
| POST | `/api/checkout/cancel` | Cancel and release inventory |
| GET | `/api/orders` | User's order history |
| GET | `/api/orders/:id` | Order details |

### Acceptance Criteria
- Inventory never goes negative even under concurrent checkouts
- Abandoned reservations auto-release after 10 minutes
- Duplicate payment submissions are safely rejected
- Order is only created after successful payment confirmation
- Full order history is queryable per user

---

## Challenge 11: Delivery with Geolocation

### Objective
Implement delivery tracking with real-time geolocation updates using Valkey Geospatial commands. Support delivery radius queries and ETA calculations.

### Technical Requirements

- **Geospatial Indexing**: Store delivery agent locations and warehouse positions using Valkey GEO commands.
- **Real-time Updates**: Delivery agents push location updates every 10 seconds.
- **Proximity Queries**: Find nearest warehouse to customer, nearest delivery agent to warehouse.
- **ETA Calculation**: Estimate delivery time based on distance and average speed.
- **Delivery Zones**: Define serviceable areas and validate delivery addresses.

### Valkey Commands & Data Structures

```
# Store warehouse locations
GEOADD warehouses 78.4347 17.4156 "HYD-WH-01"
GEOADD warehouses 78.3772 17.4435 "HYD-WH-02"
GEOADD warehouses 78.4867 17.3850 "HYD-WH-03"

# Store delivery agent locations (updated every 10s)
GEOADD delivery_agents 78.4100 17.4300 "agent_raj_001"
GEOADD delivery_agents 78.4500 17.4200 "agent_kumar_002"

# Find nearest warehouse to customer (within 15km)
GEOSEARCH warehouses FROMLONLAT 78.4347 17.4156 BYRADIUS 15 km ASC COUNT 3

# Find nearest delivery agent to warehouse
GEOSEARCH delivery_agents FROMLONLAT 78.4347 17.4156 BYRADIUS 5 km ASC COUNT 1

# Distance between agent and delivery address
GEODIST delivery_agents "agent_raj_001" "customer_location" km

# Store delivery tracking info (key = trackingId)
JSON.SET {trackingId} $ '{
  "trackingId": "DEL-HYD-98765",
  "orderId": "order:0192d4e8-5e6f-7c8d-8a0b-2c3d4e5f6a7b",
  "agentId": "agent_raj_001",
  "status": "in_transit",
  "pickupLocation": {"lat": 17.4156, "lng": 78.4347},
  "dropLocation": {"lat": 17.4300, "lng": 78.4100},
  "currentLocation": {"lat": 17.4200, "lng": 78.4200},
  "estimatedArrival": "2025-05-22T11:30:00Z",
  "history": [
    {"status": "picked_up", "timestamp": "2025-05-22T10:00:00Z", "lat": 17.4156, "lng": 78.4347},
    {"status": "in_transit", "timestamp": "2025-05-22T10:15:00Z", "lat": 17.4200, "lng": 78.4200}
  ]
}'

# Pub/Sub for real-time location updates to frontend
PUBLISH delivery:location:{trackingId} '{"lat": 17.4250, "lng": 78.4150, "eta": "11:25"}'
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/delivery/:trackingId` | Get delivery status and location |
| GET | `/api/delivery/:trackingId/track` | SSE stream for real-time updates |
| POST | `/api/delivery/:trackingId/location` | Agent pushes location update |
| GET | `/api/delivery/check-serviceability?lat=&lng=` | Check if address is serviceable |
| GET | `/api/delivery/eta?from=&to=` | Estimate delivery time |

### Acceptance Criteria
- Delivery location updates in real-time on the frontend map
- Nearest warehouse selection is correct based on customer location
- ETA updates as delivery agent moves
- Non-serviceable areas are correctly rejected
- Location history is preserved for the full delivery lifecycle

---

## Challenge 12: Rate Limiting

### Objective
Implement API rate limiting to protect services from abuse. Support multiple strategies: fixed window, sliding window, and token bucket.

### Technical Requirements

- **Per-User Limits**: Authenticated users get higher limits than anonymous users.
- **Per-Endpoint Limits**: Different endpoints have different rate limits (e.g., search: 30/min, checkout: 5/min).
- **Sliding Window**: Use a sliding window algorithm for smooth rate limiting without burst edges.
- **Response Headers**: Return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers.
- **Graceful Degradation**: Return 429 Too Many Requests with retry-after information.

### Valkey Commands & Data Structures

```
# Fixed Window (simple counter)
INCR ratelimit:{userId}:{endpoint}:{window}
EXPIRE ratelimit:{userId}:{endpoint}:{window} 60
# Check: if count > limit, reject

# Sliding Window Log (precise but memory-intensive)
ZADD ratelimit:sliding:{userId}:{endpoint} {timestamp} {requestId}
ZREMRANGEBYSCORE ratelimit:sliding:{userId}:{endpoint} 0 {timestamp - windowSize}
ZCARD ratelimit:sliding:{userId}:{endpoint}
# Check: if count > limit, reject

# Token Bucket (Lua script for atomicity)
EVAL "
  local key = KEYS[1]
  local now = tonumber(ARGV[1])
  local rate = tonumber(ARGV[2])
  local capacity = tonumber(ARGV[3])
  local requested = tonumber(ARGV[4])

  local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
  local tokens = tonumber(bucket[1]) or capacity
  local last_refill = tonumber(bucket[2]) or now

  local elapsed = now - last_refill
  local refill = math.floor(elapsed * rate)
  tokens = math.min(capacity, tokens + refill)

  if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(capacity / rate) + 1)
    return {1, tokens}
  end
  return {0, tokens}
" 1 ratelimit:bucket:{userId}:{endpoint} {now} {rate} {capacity} 1

# IP-based rate limiting for anonymous users
INCR ratelimit:ip:{clientIp}:{endpoint}:{minute}
EXPIRE ratelimit:ip:{clientIp}:{endpoint}:{minute} 60
```

### Rate Limit Configuration

```json
{
  "endpoints": {
    "/api/search": { "anonymous": 20, "authenticated": 60, "window": 60 },
    "/api/checkout/start": { "anonymous": 0, "authenticated": 5, "window": 60 },
    "/api/auth/login": { "anonymous": 5, "authenticated": 5, "window": 900 },
    "/api/products": { "anonymous": 30, "authenticated": 100, "window": 60 },
    "/api/cart/*": { "anonymous": 10, "authenticated": 30, "window": 60 }
  }
}
```

### API Response Headers

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1716372600
Retry-After: 45
Content-Type: application/json

{"error": "rate_limit_exceeded", "message": "Too many requests. Try again in 45 seconds."}
```

### Acceptance Criteria
- Rate limits are enforced per user and per endpoint
- Anonymous users have stricter limits than authenticated users
- Response headers accurately reflect remaining quota
- 429 responses include actionable retry information
- Rate limiting does not add more than 2ms latency to requests

---

## Challenge 13: Real-time Recommendations

### Objective
Build a recommendation engine that suggests products based on user behavior (collaborative filtering), browsing history, and purchase patterns using Valkey data structures.

### Technical Requirements

- **Browsing History**: Track recently viewed products per user. Use this for "Recently Viewed" and "Continue Shopping" sections.
- **Collaborative Filtering**: "Users who bought X also bought Y" — use co-purchase matrices stored in Sorted Sets.
- **Category Affinity**: Track which categories a user browses most. Weight recommendations toward preferred categories.
- **Real-time Updates**: Recommendations update immediately as new interactions occur.
- **Diversity**: Avoid recommending the same items repeatedly. Mix familiar categories with discovery.

### Valkey Commands & Data Structures

```
# Recently viewed (capped list, newest first)
LPUSH user_history:{userId} product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f
LTRIM user_history:{userId} 0 49

# Co-purchase matrix: "bought with" relationships
# When user buys productA and productB together:
ZINCRBY copurchase:{productA} 1 {productB}
ZINCRBY copurchase:{productB} 1 {productA}

# Get top co-purchased products
ZREVRANGE copurchase:{productId} 0 9 WITHSCORES

# Category affinity (weighted by recency and action type)
ZINCRBY user_affinity:{userId} 1 category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b    # view
ZINCRBY user_affinity:{userId} 3 category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b    # add to cart
ZINCRBY user_affinity:{userId} 5 category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b    # purchase

# Get user's top categories
ZREVRANGE user_affinity:{userId} 0 4 WITHSCORES

# "Frequently bought together" for product page
ZREVRANGE copurchase:product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f 0 4

# Personalized feed: combine affinity + trending + history
# Use ZUNIONSTORE with weights for blended scoring
ZUNIONSTORE recommendations:{userId} 3
  user_affinity:{userId}
  trending:global:24h
  copurchase:{lastViewedProduct}
  WEIGHTS 3 1 2

# Exclude already purchased
SDIFF recommendations:{userId} user_purchased:{userId}

# Session-based recommendations (for anonymous users)
LPUSH session_history:{sessionId} product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f
EXPIRE session_history:{sessionId} 1800
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/recommendations/personalized` | Personalized product feed |
| GET | `/api/recommendations/similar/:productId` | "Customers also bought" |
| GET | `/api/recommendations/recently-viewed` | User's browsing history |
| GET | `/api/recommendations/trending-for-you` | Trending in user's preferred categories |
| POST | `/api/recommendations/events` | Record interaction event |

### Acceptance Criteria
- Recommendations are personalized based on actual user behavior
- New interactions immediately influence recommendations
- "Bought together" suggestions are based on real co-purchase data
- Anonymous users get session-based recommendations
- Already-purchased items are excluded from suggestions

---

## Challenge 14: Agentic Search

### Objective
Build an AI-powered search experience that understands natural language queries, maintains conversation context, and can perform multi-step reasoning to find products. Combine full-text search, vector search, and structured filters into an intelligent agent.

### Technical Requirements

- **Natural Language Understanding**: Parse queries like "I need a birthday gift for my 10-year-old nephew who likes science" into structured search parameters.
- **Multi-step Reasoning**: The agent can refine results by asking clarifying questions or combining multiple searches.
- **Conversation Memory**: Maintain search context across multiple turns using Valkey (e.g., "show me cheaper options" refers to the previous search).
- **Tool Use**: The agent has access to tools: `search_products`, `filter_by_price`, `get_reviews`, `check_availability`, `get_similar`.
- **Result Explanation**: Explain why each product was recommended in the context of the user's query.

### Valkey Commands & Data Structures

```
# Store conversation context
JSON.SET conversation:{sessionId} $ '{
  "sessionId": "sess_abc123",
  "userId": "user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e",
  "turns": [
    {
      "role": "user",
      "content": "I need a birthday gift for my 10-year-old nephew who likes science",
      "timestamp": "2025-05-22T10:00:00Z"
    },
    {
      "role": "agent",
      "content": "Here are some science-themed gifts...",
      "searchParams": {
        "categories": ["category:0192d4e5-9c0d-7e1f-8a2b-3c4d5e6f7a8b", "category:0192d4e5-ad1e-7f2a-9b3c-4d5e6f7a8b9c"],
        "tags": ["science", "educational", "kids"],
        "priceRange": [500, 5000],
        "ageGroup": "8-12"
      },
      "results": ["product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f", "product:0192d4e6-3d5f-7b8c-9e0a-1b2c3d4e5f6a", "product:0192d4e6-4e6a-7c9d-8f1b-2c3d4e5f6a7b"],
      "timestamp": "2025-05-22T10:00:01Z"
    }
  ],
  "context": {
    "intent": "gift_search",
    "recipient": "nephew",
    "age": 10,
    "interests": ["science"],
    "budget": null
  }
}'
EXPIRE conversation:{sessionId} 1800

# Agent tool results cache (avoid re-running expensive searches)
SET agent_cache:{queryHash} '{...results...}' EX 300

# Search intent classification (pre-computed embeddings for intent matching)
FT.SEARCH idx:intent_vectors
  "*=>[KNN 1 @embedding $query_vec AS score]"
  PARAMS 2 query_vec {encoded_query}
  DIALECT 2

# User preference learning (long-term)
JSON.SET user_preferences:{userId} $ '{
  "pricePreference": "mid-range",
  "favoriteCategories": ["category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b", "category:0192d4e5-ad1e-7f2a-9b3c-4d5e6f7a8b9c"],
  "brandPreferences": ["Samsung", "Sony"],
  "avoidCategories": ["category:0192d4e3-7b1c-7d4e-8a2f-9c3b5d6e0f1a"]
}'
```

### Agent Tools Definition

```json
{
  "tools": [
    {
      "name": "search_products",
      "description": "Search products by keywords, category, and filters",
      "parameters": {
        "query": "string",
        "categories": "string[]",
        "tags": "string[]",
        "minPrice": "number",
        "maxPrice": "number",
        "minRating": "number"
      }
    },
    {
      "name": "semantic_search",
      "description": "Find products by meaning using vector similarity",
      "parameters": { "naturalLanguageQuery": "string", "limit": "number" }
    },
    {
      "name": "get_product_details",
      "description": "Get full details including reviews for a specific product",
      "parameters": { "productId": "string" }
    },
    {
      "name": "check_availability",
      "description": "Check if product is in stock and deliverable",
      "parameters": { "productId": "string", "postalCode": "string" }
    },
    {
      "name": "find_similar",
      "description": "Find products similar to a given product",
      "parameters": { "productId": "string", "limit": "number" }
    },
    {
      "name": "ask_clarification",
      "description": "Ask the user a clarifying question",
      "parameters": { "question": "string", "options": "string[]" }
    }
  ]
}
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agent/search` | Send natural language query to agent |
| GET | `/api/agent/conversation/:sessionId` | Get conversation history |
| POST | `/api/agent/feedback` | User feedback on results (thumbs up/down) |

### Request/Response Example

```json
// Request
{
  "sessionId": "sess_abc123",
  "message": "I need a birthday gift for my 10-year-old nephew who likes science"
}

// Response
{
  "sessionId": "sess_abc123",
  "response": "Here are some great science gifts for a 10-year-old! I focused on educational toys and experiment kits:",
  "results": [
    {
      "productId": "product:0192d4e6-5f7b-7d0e-8a2c-3d4e5f6a7b8c",
      "name": "National Geographic Science Kit",
      "price": 2499,
      "reason": "Highly rated science experiment kit designed for ages 8-12"
    },
    {
      "productId": "product:0192d4e6-6a8c-7e1f-9b3d-4e5f6a7b8c9d",
      "name": "Kids Starter Telescope",
      "price": 3999,
      "reason": "Perfect for a budding astronomer, includes star chart"
    }
  ],
  "followUp": "Would you like me to filter by a specific budget, or show options in a particular science area (chemistry, astronomy, robotics)?",
  "context": { "intent": "gift_search", "refinements_available": true }
}
```

### Acceptance Criteria
- Agent correctly interprets natural language queries into search parameters
- Conversation context is maintained across multiple turns
- "Show me cheaper options" correctly references the previous search
- Agent uses multiple tools in sequence when needed
- Results include explanations relevant to the user's stated needs
- Response time is under 3 seconds for the full agent pipeline

---

## General Guidelines

### Valkey Connection

All services should connect to Valkey at `localhost:6379` by default, configurable via environment variable:

```
VALKEY_URL=redis://localhost:6379
```

### Key Naming Convention

Since entity IDs already include the domain prefix (`user:uuid`, `product:uuid`), Valkey keys for primary entities **use the ID directly as the key**. For derived/secondary data structures, append qualifiers:

```
# Primary entity storage — the key IS the entity ID
user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e          → user JSON document
product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f       → product JSON document
order:0192d4e8-5e6f-7c8d-8a0b-2c3d4e5f6a7b         → order JSON document

# Derived data — use {purpose}:{entityId} or {purpose}:{qualifier}
cart:user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e     → user's cart hash
session:0192d4f0-1a2b-7c3d-8e4f-5a6b7c8d9e0f       → session token
trending:global:1h                                   → global trending sorted set
trending:category:0192d4e2-1f5a-7c3d-9b2e-8a4f6d0c1e3b:1h → category trending
ratelimit:user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e:/api/search:1716372600
```

This means `JSON.SET` and `JSON.GET` use the entity ID directly as the key:
```
JSON.SET product:0192d4e6-2c4e-7a6b-8d8f-0a1b2c3d4e5f $ '{...}'
JSON.GET user:0192d4e0-7b3a-7f5c-9e1a-4b8c2d6f0a1e
```

Because UUIDv7 is lexicographically sortable by time, you can use `SCAN` with a prefix pattern to find all keys for entities created in a time range, or use `ZRANGEBYLEX` on sorted sets containing prefixed UUIDv7 members.

### Error Handling

All API responses should follow this error format:

```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "details": {}
}
```

### Performance Targets

| Operation | Target Latency |
|-----------|---------------|
| Key-value read | < 1ms |
| JSON document read | < 5ms |
| Full-text search | < 10ms |
| Vector search (10K docs) | < 10ms |
| Geospatial query | < 5ms |
| Rate limit check | < 2ms |

Good luck building! 🚀
