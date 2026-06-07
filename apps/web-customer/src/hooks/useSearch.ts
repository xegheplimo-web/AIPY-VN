import { useState } from 'react';
import api from '../services/api';

export function useSearch() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const chatSearch = async (query: string, location: any, radius = 5) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/api/chat/search', {
        query,
        location,
        radius_km: radius,
      });
      setResults(res.data);
      return res.data;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { results, loading, error, chatSearch };
}
