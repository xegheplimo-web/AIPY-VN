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
  async getSystemHealth() {
    return this.request<any>('/health');
  }

  // Stores
  async getStores(params?: { status?: string; limit?: number }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ stores: any[] }>(`/api/admin/stores?${query}`);
  }

  async verifyStore(storeId: string, approved: boolean) {
    return this.request<any>(`/api/admin/stores/${storeId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ approved }),
    });
  }

  // Match Queue
  async getMatchQueue(params?: { similarity?: string }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ matches: any[] }>(`/api/admin/match-queue?${query}`);
  }

  async processMatch(matchId: string, action: 'merge' | 'approve' | 'reject') {
    return this.request<any>(`/api/admin/match-queue/${matchId}`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  }

  // Users
  async getUsers(params?: { status?: string; role?: string; search?: string }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ users: any[] }>(`/api/admin/users?${query}`);
  }

  async suspendUser(userId: string) {
    return this.request<any>(`/api/admin/users/${userId}/suspend`, {
      method: 'POST',
    });
  }

  async banUser(userId: string, reason: string) {
    return this.request<any>(`/api/admin/users/${userId}/ban`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async activateUser(userId: string) {
    return this.request<any>(`/api/admin/users/${userId}/activate`, {
      method: POST,
    });
  }

  // Reports
  async getReports(params?: { status?: string; type?: string }) {
    const query = new URLSearchParams(params as any);
    return this.request<{ reports: any[] }>(`/api/v1/reports?${query}`);
  }

  async resolveReport(reportId: string, resolutionNotes: string) {
    return this.request<any>(`/api/v1/reports/${reportId}`, {
      method: 'PUT',
      body: JSON.stringify({ status: 'resolved', resolution_notes: resolutionNotes }),
    });
  }

  async dismissReport(reportId: string, resolutionNotes: string) {
    return this.request<any>(`/api/v1/reports/${reportId}`, {
      method: 'PUT',
      body: JSON.stringify({ status: 'dismissed', resolution_notes: resolutionNotes }),
    });
  }

  // Categories
  async getCategories() {
    return this.request<{ categories: any[] }>('/api/v1/categories');
  }

  async createCategory(data: any) {
    return this.request<any>('/api/v1/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCategory(id: string, data: any) {
    return this.request<any>(`/api/v1/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCategory(id: string) {
    return this.request<any>(`/api/v1/categories/${id}`, {
      method: 'DELETE',
    });
  }
}

export const apiService = new ApiService();
export default apiService;
