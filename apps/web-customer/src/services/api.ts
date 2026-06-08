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
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  private getAuthHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }));
      throw new Error(error.message || `API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string; user: User }>(
      '/api/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }
    );
  }

  async register(data: { email: string; password: string; full_name?: string; phone?: string }) {
    return this.request<{ access_token: string; refresh_token: string; user: User }>(
      '/api/auth/register',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async logout() {
    this.clearToken();
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
  async getCart(): Promise<{ items: CartItem[] }> {
    return this.request<{ items: CartItem[] }>('/api/cart');
  }

  async addToCart(productId: string, quantity: number = 1): Promise<{ items: CartItem[] }> {
    return this.request<{ items: CartItem[] }>('/api/cart', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  }

  async updateCartItem(itemId: string, quantity: number): Promise<{ items: CartItem[] }> {
    return this.request<{ items: CartItem[] }>(`/api/cart/items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity }),
    });
  }

  async removeFromCart(itemId: string): Promise<{ items: CartItem[] }> {
    return this.request<{ items: CartItem[] }>(`/api/cart/items/${itemId}`, {
      method: 'DELETE',
    });
  }

  // Orders
  async createOrder(data: {
    store_id: string;
    items: Array<{ product_id: string; quantity: number; unit_price: number }>;
    delivery_method: 'pickup' | 'delivery';
    shipping_address?: string;
    customer_name?: string;
    customer_phone?: string;
    customer_email?: string;
    notes?: string;
    payment_method?: string;
  }): Promise<Order> {
    return this.request<Order>('/api/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getOrders(): Promise<{ orders: Order[] }> {
    return this.request<{ orders: Order[] }>('/api/orders');
  }

  async getOrder(id: string): Promise<Order> {
    return this.request<Order>(`/api/orders/${id}`);
  }

  // Geo
  async getNearbyStores(lat: number, lng: number, radiusKm: number = 5): Promise<Store[]> {
    return this.request<Store[]>(`/api/geo/nearby?lat=${lat}&lng=${lng}&radius_km=${radiusKm}`);
  }

  // Promotions
  async validatePromotion(code: string, orderAmount: number) {
    return this.request<{ valid: boolean; discount: number; type: string }>(
      `/api/v1/promotions/validate/${code}?order_amount=${orderAmount}`
    );
  }
}

export const apiService = new ApiService();
export default apiService;
