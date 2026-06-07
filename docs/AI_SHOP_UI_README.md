# AI-SHOP.VN UI

Giao diện demo đầy đủ cho AI-SHOP.VN: Customer App, Search Result, Product Detail, Cart/Checkout, Order Tracking, Chat Store, Owner Dashboard, Admin Dashboard.

## Chạy dự án

```bash
npm install
npm run dev
```

Mở: http://localhost:5173

## Build production

```bash
npm run build
npm run preview
```

## Gắn API thật sau này

Các màn hình hiện dùng mock data trong `src/data/mock.ts`. Khi có backend, thay phần data bằng API client:

- `POST /api/chat/search`
- `GET /api/stores/:id`
- `GET /api/products/:id`
- `POST /api/cart/items`
- `POST /api/orders`
- `GET /api/owner/analytics/summary`
- `GET /api/admin/stats`
