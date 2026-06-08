import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

export type OrderStatus = 'pending' | 'confirmed' | 'preparing' | 'ready' | 'completed' | 'cancelled';

export interface OrderItem {
  product_id: string;
  product_name: string;
  product_image?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Order {
  id: string;
  order_number: string;
  status: OrderStatus;
  created_at: string;
  updated_at?: string;
  items: OrderItem[];
  total_amount: number;
  shipping_fee: number;
  discount_amount: number;
  final_amount: number;
  delivery_address?: string;
  delivery_method: 'pickup' | 'standard' | 'express';
  payment_method: 'cod' | 'momo' | 'zalopay';
  store_name?: string;
  store_logo?: string;
}

export const statusLabels: Record<OrderStatus, string> = {
  pending: 'Chờ xác nhận',
  confirmed: 'Đã xác nhận',
  preparing: 'Đang chuẩn bị',
  ready: 'Sẵn sàng',
  completed: 'Hoàn thành',
  cancelled: 'Đã hủy',
};

export const statusTimeline: OrderStatus[] = ['pending', 'confirmed', 'preparing', 'ready', 'completed'];

export function useOrders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.get('/api/users/me/orders');
      setOrders(res.data.orders || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Không thể tải đơn hàng');
      setOrders([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const getOrderById = useCallback((orderId: string) => {
    return orders.find((o) => o.id === orderId) || null;
  }, [orders]);

  return {
    orders,
    loading,
    error,
    fetchOrders,
    getOrderById,
  };
}
