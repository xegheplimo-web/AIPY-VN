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

interface RequestConfig extends RequestInit {
  retry?: number;
  timeout?: number;
}

interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

class ApiService {
  private token: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing: boolean = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  setRefreshToken(token: string) {
    this.refreshToken = token;
    localStorage.setItem('refresh_token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  }

  getRefreshToken(): string | null {
    if (!this.refreshToken) {
      this.refreshToken = localStorage.getItem('refresh_token');
    }
    return this.refreshToken;
  }

  clearToken() {
    this.token = null;
    this.refreshToken = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
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

  private async refreshTokenIfNeeded(): Promise<string | null> {
    if (this.isRefreshing) {
      return new Promise((resolve) => {
        this.refreshSubscribers.push(resolve);
      });
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    this.isRefreshing = true;

    try {
      const response = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      this.setToken(data.access_token);
      this.setRefreshToken(data.refresh_token);

      // Notify all waiting requests
      this.refreshSubscribers.forEach((callback) => callback(data.access_token));
      this.refreshSubscribers = [];

      return data.access_token;
    } catch (error) {
      this.clearToken();
      this.refreshSubscribers.forEach((callback) => callback(null));
      this.refreshSubscribers = [];
      return null;
    } finally {
      this.isRefreshing = false;
    }
  }

  private async requestWithRetry<T>(
    url: string,
    options: RequestConfig,
    retryCount: number = 0
  ): Promise<T> {
    const maxRetries = options.retry || 3;
    const timeout = options.timeout || 30000;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // Try to refresh token on 401
        if (response.status === 401 && !url.includes('/auth/')) {
          const newToken = await this.refreshTokenIfNeeded();
          if (newToken) {
            // Retry with new token
            options.headers = {
              ...options.headers,
              Authorization: `Bearer ${newToken}`,
            };
            return this.requestWithRetry<T>(url, options, retryCount);
          }
        }

        // Retry on 5xx errors
        if (response.status >= 500 && retryCount < maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, 1000 * (retryCount + 1)));
          return this.requestWithRetry<T>(url, options, retryCount + 1);
        }

        const error: ApiError = await response.json().catch(() => ({
          message: 'Unknown error',
          status: response.status,
        }));
        throw new Error(error.message || `API Error: ${response.status} ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }

      // Retry on network errors
      if (retryCount < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * (retryCount + 1)));
        return this.requestWithRetry<T>(url, options, retryCount + 1);
      }

      throw error;
    }
  }

  private async request<T>(endpoint: string, options: RequestConfig = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    return this.requestWithRetry<T>(url, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    });
  }

  // Auth
  async login(email: string, password: string) {
    const response = await this.request<{
      access_token: string;
      refresh_token: string;
      user: User;
    }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    this.setToken(response.access_token);
    this.setRefreshToken(response.refresh_token);

    return response;
  }

  async register(data: { email: string; password: string; full_name?: string; phone?: string }) {
    const response = await this.request<{
      access_token: string;
      refresh_token: string;
      user: User;
    }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    this.setToken(response.access_token);
    this.setRefreshToken(response.refresh_token);

    return response;
  }

  async logout() {
    try {
      await this.request('/api/auth/logout', { method: 'POST' });
    } finally {
      this.clearToken();
    }
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

  async clearCart(): Promise<{ items: CartItem[] }> {
    return this.request<{ items: CartItem[] }>('/api/cart', {
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

  async getOrders(params?: {
    status?: string;
    limit?: number;
    page?: number;
  }): Promise<{ orders: Order[]; total: number; page: number; limit: number }> {
    const query = new URLSearchParams(params as any);
    return this.request<{ orders: Order[]; total: number; page: number; limit: number }>(
      `/api/orders?${query}`
    );
  }

  async getOrder(id: string): Promise<Order> {
    return this.request<Order>(`/api/orders/${id}`);
  }

  async cancelOrder(id: string): Promise<Order> {
    return this.request<Order>(`/api/orders/${id}/cancel`, {
      method: 'POST',
    });
  }

  // User Profile
  async getProfile(): Promise<User> {
    return this.request<User>('/api/users/me');
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return this.request<User>('/api/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async addAddress(data: Omit<Address, 'id'>): Promise<Address> {
    return this.request<Address>('/api/users/me/addresses', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAddress(id: string, data: Partial<Address>): Promise<Address> {
    return this.request<Address>(`/api/users/me/addresses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAddress(id: string): Promise<void> {
    return this.request<void>(`/api/users/me/addresses/${id}`, {
      method: 'DELETE',
    });
  }

  // Favorites
  async getFavorites(): Promise<Product[]> {
    return this.request<Product[]>('/api/favorites');
  }

  async addFavorite(productId: string): Promise<Product[]> {
    return this.request<Product[]>('/api/favorites', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId }),
    });
  }

  async removeFavorite(productId: string): Promise<Product[]> {
    return this.request<Product[]>(`/api/favorites/${productId}`, {
      method: 'DELETE',
    });
  }

  // Reviews
  async getReviews(productId: string): Promise<any[]> {
    return this.request<any[]>(`/api/reviews/product/${productId}`);
  }

  async addReview(productId: string, data: { rating: number; comment: string }): Promise<any> {
    return this.request<any>(`/api/reviews/product/${productId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
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

  async getActivePromotions(): Promise<any[]> {
    return this.request<any[]>('/api/v1/promotions/active');
  }

  // Reports
  async createReport(data: {
    target_type: 'product' | 'store' | 'user';
    target_id: string;
    reason: string;
    description?: string;
  }): Promise<any> {
    return this.request<any>('/api/v1/reports', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const apiService = new ApiService();
export default apiService;
