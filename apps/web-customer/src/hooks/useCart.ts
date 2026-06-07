import { useCallback, useEffect, useState } from 'react';
import api from '../services/api';

export interface CartItem {
  id: string;
  product_id: string;
  name: string;
  image_url?: string;
  price: number;
  quantity: number;
  stock: number;
  unit?: string;
  store_id: string;
  store_name: string;
  store_logo?: string;
}

export interface CartStoreGroup {
  store_id: string;
  store_name: string;
  store_logo?: string;
  items: CartItem[];
  subtotal: number;
}

const LOCAL_CART_KEY = 'vietstore_cart';

function getLocalCart(): CartItem[] {
  try {
    const data = localStorage.getItem(LOCAL_CART_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

function setLocalCart(items: CartItem[]) {
  localStorage.setItem(LOCAL_CART_KEY, JSON.stringify(items));
}

export function useCart() {
  const [items, setItems] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCart = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/cart/');
      const fetchedItems: CartItem[] = res.data.items || [];
      setItems(fetchedItems);
      setLocalCart(fetchedItems);
    } catch (err: any) {
      const local = getLocalCart();
      setItems(local);
      if (err.response?.status === 401) {
        setError('Phiên đăng nhập hết hạn, vui lòng đăng nhập lại');
      } else if (err.response?.status === 500) {
        setError('Lỗi server, vui lòng thử lại sau');
      } else {
        setError(err.response?.data?.detail || 'Không thể tải giỏ hàng, dùng dữ liệu local');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addItem = useCallback(async (productId: string, quantity = 1) => {
    try {
      const res = await api.post('/api/cart/items', { product_id: productId, quantity });
      const updated: CartItem[] = res.data.items || [];
      setItems(updated);
      setLocalCart(updated);
      return true;
    } catch (err: any) {
      // Fallback: add to localStorage
      const local = getLocalCart();
      const existing = local.find((i) => i.product_id === productId);
      let updated: CartItem[];
      if (existing) {
        updated = local.map((i) =>
          i.product_id === productId ? { ...i, quantity: i.quantity + quantity } : i
        );
      } else {
        updated = [
          ...local,
          {
            id: `local-${Date.now()}`,
            product_id: productId,
            name: '',
            price: 0,
            quantity,
            stock: 999,
            store_id: '',
            store_name: '',
          },
        ];
      }
      setItems(updated);
      setLocalCart(updated);
      if (err.response?.status === 401) {
        setError('Phiên đăng nhập hết hạn, vui lòng đăng nhập lại');
      } else if (err.response?.status === 400) {
        setError('Sản phẩm không còn hàng hoặc số lượng không hợp lệ');
      } else {
        setError(err.response?.data?.detail || 'Lỗi thêm vào giỏ hàng');
      }
      return false;
    }
  }, []);

  const updateQuantity = useCallback(async (itemId: string, quantity: number) => {
    if (quantity < 1) return removeItem(itemId);
    try {
      const res = await api.put(`/api/cart/items/${itemId}`, { quantity });
      const updated: CartItem[] = res.data.items || [];
      setItems(updated);
      setLocalCart(updated);
    } catch (err: any) {
      const local = getLocalCart().map((i) =>
        i.id === itemId || i.product_id === itemId ? { ...i, quantity } : i
      );
      setItems(local);
      setLocalCart(local);
      setError(err.response?.data?.detail || 'Lỗi cập nhật số lượng');
    }
  }, []);

  const removeItem = useCallback(async (itemId: string) => {
    try {
      const res = await api.delete(`/api/cart/items/${itemId}`);
      const updated: CartItem[] = res.data.items || [];
      setItems(updated);
      setLocalCart(updated);
    } catch {
      const local = getLocalCart().filter((i) => i.id !== itemId && i.product_id !== itemId);
      setItems(local);
      setLocalCart(local);
    }
  }, []);

  const clearCart = useCallback(() => {
    setItems([]);
    setLocalCart([]);
  }, []);

  const groupedByStore = useCallback((): CartStoreGroup[] => {
    const map: Record<string, CartStoreGroup> = {};
    items.forEach((item) => {
      if (!map[item.store_id]) {
        map[item.store_id] = {
          store_id: item.store_id,
          store_name: item.store_name,
          store_logo: item.store_logo,
          items: [],
          subtotal: 0,
        };
      }
      map[item.store_id].items.push(item);
      map[item.store_id].subtotal += item.price * item.quantity;
    });
    return Object.values(map);
  }, [items]);

  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const count = items.reduce((sum, item) => sum + item.quantity, 0);

  return {
    items,
    groupedByStore: groupedByStore(),
    total,
    count,
    loading,
    error,
    fetchCart,
    addItem,
    updateQuantity,
    removeItem,
    clearCart,
  };
}
