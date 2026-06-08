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

  // Generic HTTP methods for backward compatibility
  async get<T>(endpoint: string, options?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, body?: any, options?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body: body ? JSON.stringify(body) : undefined });
  }

  async put<T>(endpoint: string, body?: any, options?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body: body ? JSON.stringify(body) : undefined });
  }

  async delete<T>(endpoint: string, options?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  // Auth
  async login(email: string, password: string) {
    const response = await this.request<{
      access_token: string;
      refresh_token: string;
      user: any;
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
      user: any;
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

  // Dashboard
  async getDashboardStats() {
    return this.request<{
      revenue: number;
      orders: number;
      products: number;
      customers: number;
    }>('/api/owner/dashboard');
  }

  // Products
  async getProducts(params?: { limit?: number; page?: number; search?: string }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ products: any[]; total: number; page: number; limit: number }>(
      `/api/owner/products?${query}`
    );
  }

  async getProduct(id: string) {
    return this.request<any>(`/api/owner/products/${id}`);
  }

  async createProduct(data: any) {
    return this.request<any>('/api/owner/products', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProduct(id: string, data: any) {
    return this.request<any>(`/api/owner/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProduct(id: string) {
    return this.request<any>(`/api/owner/products/${id}`, {
      method: 'DELETE',
    });
  }

  // Orders
  async getOrders(params?: {
    status?: string;
    limit?: number;
    page?: number;
    from_date?: string;
    to_date?: string;
  }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ orders: any[]; total: number; page: number; limit: number }>(
      `/api/owner/orders?${query}`
    );
  }

  async getOrder(id: string) {
    return this.request<any>(`/api/owner/orders/${id}`);
  }

  async updateOrderStatus(id: string, status: string) {
    return this.request<any>(`/api/owner/orders/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // Promotions
  async getPromotions(params?: { status?: string; limit?: number; page?: number }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ promotions: any[]; total: number; page: number; limit: number }>(
      `/api/v1/promotions?${query}`
    );
  }

  async getPromotion(id: string) {
    return this.request<any>(`/api/v1/promotions/${id}`);
  }

  async createPromotion(data: any) {
    return this.request<any>('/api/v1/promotions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePromotion(id: string, data: any) {
    return this.request<any>(`/api/v1/promotions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deletePromotion(id: string) {
    return this.request<any>(`/api/v1/promotions/${id}`, {
      method: 'DELETE',
    });
  }

  // Chat
  async getChatMessages(customerId: string) {
    return this.request<{ messages: any[] }>(`/api/chat/${customerId}`);
  }

  async sendChatMessage(customerId: string, content: string) {
    return this.request<any>(`/api/chat/${customerId}`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // Analytics
  async getAnalytics(params?: { from_date?: string; to_date?: string }) {
    const query = new URLSearchParams(params as any);
    return this.request<any>(`/api/owner/analytics?${query}`);
  }

  // Store Settings
  async getStoreSettings() {
    return this.request<any>('/api/owner/settings');
  }

  async updateStoreSettings(data: any) {
    return this.request<any>('/api/owner/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // File Upload
  async uploadFile(file: File, type: 'product' | 'store' = 'product') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    return response.json();
  }
}

export const apiService = new ApiService();
export default apiService;
