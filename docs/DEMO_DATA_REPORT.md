# Báo Cáo Kiểm Tra Demo Data trong Dự Án AIPY-VN

## 📋 Tóm tắt

Đã tìm thấy **7 phần** đang sử dụng mock/demo data cần chuyển sang API thực tế.

---

## 🔍 Danh Sách Demo Data

### 1. **web-customer/src/pages/DemoPage.tsx** ⚠️ CẢNH BÁO
- **Trạng thái**: Cả trang là demo
- **Mock data**: `sampleStores` array (dòng 29-68)
- **Dữ liệu**: 3 cửa hàng mẫu với sản phẩm
- **Hành động**: 
  - Hiển thị danh sách cửa hàng
  - Thêm vào giỏ hàng (mock)
  - Liên hệ (mock)
- **Ưu tiên**: **CAO** - Cần xóa hoặc chuyển sang trang thực tế

### 2. **web-admin/src/pages/StoreVerificationPage.tsx**
- **Trạng thái**: Có mock data
- **Mock data**: `mockData` array (dòng 42-86)
- **Dữ liệu**: 3 cửa hàng cần verification
- **Hành động**:
  - Load verifications (mock)
  - Approve/Reject (mock)
- **API cần**: GET /api/admin/stores/pending, POST /api/admin/stores/{id}/verify
- **Ưu tiên**: **CAO** - Chức năng quan trọng của admin

### 3. **web-owner/src/pages/PromotionsPage.tsx**
- **Trạng thái**: Có mock data
- **Mock data**: `mockPromotions` array (dòng 56-116)
- **Dữ liệu**: 4 promotions mẫu
- **Hành động**:
  - Load promotions (mock)
  - Add/Edit/Delete (mock)
- **API cần**: GET /api/v1/promotions, POST /api/v1/promotions, PUT /api/v1/promotions/{id}, DELETE /api/v1/promotions/{id}
- **Ưu tiên**: **TRUNG BÌNH** - Chức năng quan trọng

### 4. **web-owner/src/pages/OwnerChatPage.tsx**
- **Trạng thái**: Có mock data
- **Mock data**: 
  - `mockCustomers` array (dòng 65-90)
  - `mockMessages` array (dòng 102-125)
- **Dữ liệu**: 3 customers, 3 messages mẫu
- **Hành động**:
  - Load customers (mock)
  - Load messages (mock)
  - Send message (mock)
- **API cần**: WebSocket hoặc REST API cho chat
- **Ưu tiên**: **TRUNG BÌNH** - Chức năng chat quan trọng

### 5. **web-owner/src/pages/OwnerAnalyticsPage.tsx**
- **Trạng thái**: Có mock data
- **Mock data**:
  - `topProducts` array (dòng 43-48)
  - `searchQueries` array (dòng 51-56)
  - `hourlyData` array (dòng 59-71)
  - `categoryData` array (dòng 74-79)
- **Dữ liệu**: Analytics mẫu
- **Hành động**: Hiển thị biểu chart (mock)
- **API cần**: GET /api/admin/analytics
- **Ưu tiên**: **THẤP** - Chỉ hiển thị, có thể giữ mock cho demo

### 6. **web-owner/src/pages/OwnerOrdersPage.tsx**
- **Trạng thái**: Có mock data
- **Mock data**: `orders` array (dòng 28-36)
- **Dữ liệu**: 2 orders mẫu
- **Hành động**: Hiển thị danh sách orders (mock)
- **API cần**: GET /api/owner/orders
- **Ưu tiên**: **CAO** - Chức năng quan trọng của owner

### 7. **web-owner/src/pages/OwnerDashboardPage.tsx**
- **Trạng thái**: Có mock data
- **Mock data**: `stats` array (dòng 6-10)
- **Dữ liệu**: 4 stats mẫu
- **Hành động**: Hiển thị dashboard stats (mock)
- **API cần**: GET /api/owner/dashboard
- **Ưu tiên**: **CAO** - Dashboard quan trọng

---

## 🎯 Kế Hoạch Chuyển Đổi

### Priority 1: CAO (Cần làm ngay)

1. **Xóa DemoPage.tsx** hoặc chuyển sang trang SearchPage thực tế
2. **StoreVerificationPage** - Kết nối API admin stores
3. **OwnerOrdersPage** - Kết nối API owner orders
4. **OwnerDashboardPage** - Kết nối API owner dashboard

### Priority 2: TRUNG BÌNH

5. **PromotionsPage** - Kết nối API promotions
6. **OwnerChatPage** - Kết nối WebSocket chat

### Priority 3: THẤP (Có thể giữ mock)

7. **OwnerAnalyticsPage** - Có thể giữ mock cho demo UI

---

## 📝 API Endpoints Đã Có

Theo kiểm tra, các API endpoints sau đã có sẵn:

- ✅ `/api/admin/stores` - Store management
- ✅ `/api/admin/stores/{id}/verify` - Store verification
- ✅ `/api/owner/orders` - Owner orders
- ✅ `/api/v1/promotions` - Promotions
- ✅ `/api/admin/analytics` - Analytics
- ✅ `/api/owner/dashboard` - Owner dashboard

---

## 🔧 Cần Làm

### 1. Xóa DemoPage.tsx
```bash
rm apps/web-customer/src/pages/DemoPage.tsx
```
Cập nhật routing để không trỏ đến DemoPage.

### 2. StoreVerificationPage
Thay mock data bằng API call:
```typescript
const loadVerifications = async () => {
  try {
    const response = await api.getStores({ status: 'pending' });
    setVerifications(response.stores);
  } catch (err) {
    console.error('Failed to load verifications:', err);
  } finally {
    setLoading(false);
  }
};
```

### 3. OwnerOrdersPage
Thay mock orders bằng API call:
```typescript
const loadOrders = async () => {
  try {
    const response = await api.getOrders();
    setOrders(response.orders);
  } catch (err) {
    console.error('Failed to load orders:', err);
  }
};
```

### 4. OwnerDashboardPage
Thay mock stats bằng API call:
```typescript
const loadStats = async () => {
  try {
    const response = await api.getDashboardStats();
    setStats(response);
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
};
```

### 5. PromotionsPage
Thay mock promotions bằng API call:
```typescript
const loadPromotions = async () => {
  try {
    const response = await api.getPromotions();
    setPromotions(response.promotions);
  } catch (err) {
    console.error('Failed to load promotions:', err);
  }
};
```

### 6. OwnerChatPage
Thay mock customers/messages bằng API call:
```typescript
const loadCustomers = async () => {
  try {
    const response = await api.getCustomers();
    setCustomers(response.customers);
  } catch (err) {
    console.error('Failed to load customers:', err);
  }
};
```

---

## ✅ Kiểm Tra

Sau khi chuyển đổi:
1. Test từng trang để đảm bảo API hoạt động
2. Kiểm tra error handling khi API fail
3. Thêm loading states
4. Thêm empty states khi không có data
5. Test với dữ liệu thực từ database

---

## 📊 Tiến Độ

- **Đã tích hợp API**: ✅ Backend đã có đầy đủ endpoints
- **Cần chuyển frontend**: 7 trang
- **Ưu tiên cao**: 4 trang
- **Ưu tiên trung bình**: 2 trang
- **Có thể giữ mock**: 1 trang
