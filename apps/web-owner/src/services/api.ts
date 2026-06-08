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
    return this.request<{ access_token: string; refresh_token: string; user: any }>(
      '/api/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }
    );
  }

  async register(data: { email: string; password: string; full_name?: string; phone?: string }) {
    return this.request<{ access_token: string; refresh_token: string; user: any }>(
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
  async getProducts(params?: { limit?: number; page?: number }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ products: any[] }>(`/api/owner/products?${query}`);
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
  async getOrders(params?: { status?: string; limit?: number }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ orders: any[] }>(`/api/owner/orders?${query}`);
  }

  async updateOrderStatus(id: string, status: string) {
    return this.request<any>(`/api/owner/orders/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // Promotions
  async getPromotions(params?: { status?: string }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ promotions: any[] }>(`/api/v1/promotions?${query}`);
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
}

export const apiService = new ApiService();
export default apiService;
