import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export interface Store {
  id: string;
  name: string;
  address: string;
  phone?: string;
  email?: string;
  logo_url?: string;
  cover_image_url?: string;
  rating: number;
  total_reviews: number;
  latitude?: number;
  longitude?: number;
  map_url?: string;
  business_hours?: string;
  is_open_now?: boolean;
}

export interface StoreProduct {
  id: string;
  name: string;
  category: string;
  price: number;
  unit?: string;
  stock: number;
  images?: string[];
  shelf_location?: string;
  brand?: string;
  description?: string;
}

export interface StoreDetail extends Store {
  products: StoreProduct[];
}

export function useStore(storeId?: string) {
  const [store, setStore] = useState<StoreDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStore = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/api/stores/${id}`);
      setStore(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Không thể tải thông tin cửa hàng');
      setStore(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (storeId) {
      fetchStore(storeId);
    }
  }, [storeId, fetchStore]);

  return { store, loading, error, fetchStore };
}
