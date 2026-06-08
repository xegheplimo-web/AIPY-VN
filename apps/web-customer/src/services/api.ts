// API Response Types
export interface SearchProductResult {
  id: string;
  name: string;
  price: number | null;
  stock: number;
  in_stock: boolean;
  shelf_location: string;
  category: string | null;
}

export interface SearchStoreResult {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  distance_m: number | null;
  logo_url: string | null;
  cover_image_url: string | null;
  rating: number | null;
  total_reviews: number | null;
  is_open_now: boolean | null;
  industry: string | null;
  map_url: string;
  products: SearchProductResult[];
}

export interface ChatSearchResponse {
  summary: string;
  stores: SearchStoreResult[];
  total_found: number;
}

export interface ChatSearchRequest {
  query: string;
  location?: {
    lat: number;
    lng: number;
  };
  radius_km: number;
  limit: number;
}

export interface Store {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  phone: string | null;
  email: string | null;
  zalo: string | null;
  logo_url: string | null;
  cover_image_url: string | null;
  business_hours: Record<string, any> | null;
  rating: number | null;
  review_count: number | null;
  is_open_now: boolean;
  industry: string | null;
  distance_m?: number;
}

export interface Product {
  id: string;
  name: string;
  price: number | null;
  stock: number;
  shelf_location: string;
  category: string | null;
  store_id: string;
  store?: Store;
  images: string[];
  description: string | null;
}

export interface CartItem {
  product: Product;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: string;
  user_id: string;
  store_id: string;
  status: string;
  total_amount: number;
  shipping_fee: number;
  delivery_method: 'pickup' | 'delivery';
  created_at: string;
  items: OrderItem[];
}

export interface OrderItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  phone: string | null;
  addresses: Address[];
}

export interface Address {
  id: string;
  full_address: string;
  latitude: number;
  longitude: number;
  is_default: boolean;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:9000';

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Search
  async chatSearch(request: ChatSearchRequest): Promise<ChatSearchResponse> {
    return this.request<ChatSearchResponse>('/api/chat/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getSuggestions(query: string, limit: number = 5): Promise<{ suggestions: string[] }> {
    return this.request<{ suggestions: string[] }>(`/api/suggestions?q=${query}&limit=${limit}`);
  }

  // Stores
  async getStores(): Promise<Store[]> {
    return this.request<Store[]>('/api/stores');
  }

  async getStore(id: string): Promise<Store> {
    return this.request<Store>(`/api/stores/${id}`);
  }

  // Products
  async getProduct(id: string): Promise<Product> {
    return this.request<Product>(`/api/products/${id}`);
  }

  async getStoreProducts(storeId: string): Promise<Product[]> {
    return this.request<Product[]>(`/api/stores/${storeId}/products`);
  }

  // Cart
  async getCart(): Promise<CartItem[]> {
    return this.request<CartItem[]>('/api/cart');
  }

  async addToCart(productId: string, quantity: number = 1): Promise<CartItem[]> {
    return this.request<CartItem[]>('/api/cart', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  }

  async updateCartItem(productId: string, quantity: number): Promise<CartItem[]> {
    return this.request<CartItem[]>('/api/cart', {
      method: 'PUT',
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  }

  async removeFromCart(productId: string): Promise<CartItem[]> {
    return this.request<CartItem[]>(`/api/cart/${productId}`, {
      method: 'DELETE',
    });
  }

  // Orders
  async createOrder(data: {
    store_id: string;
    items: Array<{ product_id: string; quantity: number; unit_price: number }>;
    delivery_method: 'pickup' | 'delivery';
    shipping_address?: string;
  }): Promise<Order> {
    return this.request<Order>('/api/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getOrders(): Promise<Order[]> {
    return this.request<Order[]>('/api/orders');
  }

  async getOrder(id: string): Promise<Order> {
    return this.request<Order>(`/api/orders/${id}`);
  }

  // Geo
  async getNearbyStores(lat: number, lng: number, radiusKm: number = 5): Promise<Store[]> {
    return this.request<Store[]>(`/api/geo/nearby?lat=${lat}&lng=${lng}&radius_km=${radiusKm}`);
  }
}

export const apiService = new ApiService();
export default apiService;
