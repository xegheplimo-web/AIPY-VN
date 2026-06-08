import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

export interface Product {
  id: string;
  name: string;
  description?: string;
  price: number;
  original_price?: number;
  unit?: string;
  stock: number;
  brand?: string;
  category?: string;
  images: string[];
  shelf_location?: string;
  store_id: string;
  store_name?: string;
  store_logo?: string;
  rating?: number;
  total_reviews?: number;
}

export interface ProductAlternative {
  id: string;
  name: string;
  price: number;
  unit?: string;
  stock: number;
  images?: string[];
  store_id: string;
  store_name?: string;
  similarity_score?: number;
}

export function useProduct(productId?: string) {
  const [product, setProduct] = useState<Product | null>(null);
  const [alternatives, setAlternatives] = useState<ProductAlternative[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProduct = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.get(`/api/products/${id}`);
      setProduct(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Không thể tải thông tin sản phẩm');
      setProduct(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAlternatives = useCallback(async (id: string) => {
    try {
      const res = await apiService.get(`/api/products/${id}/alternatives`);
      setAlternatives(res.data.alternatives || []);
    } catch {
      setAlternatives([]);
    }
  }, []);

  useEffect(() => {
    if (productId) {
      fetchProduct(productId);
      fetchAlternatives(productId);
    }
  }, [productId, fetchProduct, fetchAlternatives]);

  return {
    product,
    alternatives,
    loading,
    error,
    fetchProduct,
    fetchAlternatives,
  };
}
