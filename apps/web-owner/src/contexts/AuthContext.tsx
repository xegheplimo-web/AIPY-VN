import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiService from '../services/api';

interface User {
  id: string;
  email: string;
  name: string | null;
  phone: string | null;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name?: string; phone?: string }) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    const token = localStorage.getItem('auth_token');
    if (token) {
      apiService.setToken(token);
      // Fetch real user info from API
      apiService.getProfile().then((profile) => {
        const userData = {
          id: profile.id,
          email: profile.email,
          name: profile.name,
          phone: profile.phone,
          role: profile.role || 'owner',
        };
        setUser(userData);
        // Store store_id if available
        if (profile.store_id) {
          localStorage.setItem('store_id', profile.store_id);
        }
      }).catch(() => {
        // Token is invalid, clear it
        apiService.clearToken();
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('store_id');
      }).finally(() => {
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await apiService.login(email, password);
      apiService.setToken(response.access_token);
      setUser(response.user);
      // Store store_id if available from login response
      if (response.user?.store_id) {
        localStorage.setItem('store_id', response.user.store_id);
      }
    } catch (error) {
      throw error;
    }
  };

  const register = async (data: { email: string; password: string; full_name?: string; phone?: string }) => {
    try {
      const response = await apiService.register(data);
      apiService.setToken(response.access_token);
      setUser(response.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
    localStorage.removeItem('store_id');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
