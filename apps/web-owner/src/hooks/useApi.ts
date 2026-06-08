import { useState, useCallback } from 'react';
import { apiService } from '../services/api';

interface UseApiOptions<T> {
  initialData?: T;
}

export function useApi<T>(endpoint: string, options: UseApiOptions<T> = {}) {
  const [data, setData] = useState<T | undefined>(options.initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.get(endpoint);
      setData(res);
      return res;
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  const post = useCallback(
    async (body: unknown) => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiService.post(endpoint, body);
        return res;
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [endpoint]
  );

  return { data, loading, error, fetch, post };
}
