import { useState } from 'react';
import StoreCard from './StoreCard';

interface SearchResultsProps {
  query: string;
  userLocation?: any;
  results: any[];
}

export default function SearchResults({ query, userLocation, results }: SearchResultsProps) {
  const [cart, setCart] = useState([]);

  const addToCart = (product: any, store: any, quantity = 1) => {
    setCart((prev: any) => [...prev, { product, store, quantity, unit_price: product.price }]);
  };

  return (
    <div className="space-y-6 p-4">
      <div className="bg-blue-50 p-4 rounded-xl">
        <h2 className="font-semibold text-lg">
          🔍 Kết quả cho "{query}"
        </h2>
        <p className="text-sm text-gray-600">
          Tìm thấy {results.length} cửa hàng • Sắp xếp theo khoảng cách
        </p>
      </div>

      {results.map((store) => (
        <StoreCard key={store.id} store={store} userLocation={userLocation} />
      ))}

      {cart.length > 0 && (
        <div className="fixed bottom-6 right-6 z-50">
          <a
            href="/cart"
            className="flex items-center gap-3 px-6 py-4 bg-orange-600 text-white rounded-full shadow-2xl hover:bg-orange-700 transition"
          >
            🛒 Giỏ hàng ({cart.length})
            <span className="font-bold">
              {cart.reduce((sum: number, item: any) => sum + (item.unit_price * item.quantity), 0).toLocaleString('vi-VN')}đ
            </span>
          </a>
        </div>
      )}
    </div>
  );
}
