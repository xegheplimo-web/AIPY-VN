import { MapPin, Navigation, ShoppingCart, Store } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { SearchStoreResult } from '../../services/api';
import { formatDistance } from '../../utils/distance';
import { formatMoney } from '../../utils/money';

interface StoreResultCardProps {
  store: SearchStoreResult;
  onAddToCart?: (storeId: string, productId: string) => void;
  onOpenMap?: (store: SearchStoreResult) => void;
  onOpenStore?: () => void;
  compact?: boolean;
}

export default function StoreResultCard({
  store,
  onAddToCart,
  onOpenMap,
  onOpenStore,
  compact = false,
}: StoreResultCardProps) {
  const navigate = useNavigate();
  const product = store.products[0];

  return (
    <article className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      {/* Cover Image */}
      {store.cover_image_url && (
        <img
          src={store.cover_image_url}
          alt={store.name}
          className="w-full h-32 object-cover"
        />
      )}

      <div className="p-4">
        {/* Store Info */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {store.logo_url ? (
              <img src={store.logo_url} alt="" className="w-8 h-8 rounded-full object-cover" />
            ) : (
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Store className="w-4 h-4 text-blue-600" />
              </div>
            )}
            <div className="min-w-0">
              <h4 className="font-semibold text-gray-900 text-sm truncate">{store.name}</h4>
              <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-500">
                <MapPin size={11} />
                <span className="truncate">{store.address}</span>
              </div>
            </div>
          </div>
          {store.distance_m !== null && store.distance_m !== undefined && (
            <span className="ml-2 px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium whitespace-nowrap">
              {formatDistance(store.distance_m)}
            </span>
          )}
        </div>

        {/* Product Preview */}
        {product && (
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mb-3">
            <div className="w-14 h-14 bg-white rounded-lg flex items-center justify-center flex-shrink-0">
              {product.images?.[0] ? (
                <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover rounded-lg" />
              ) : (
                <ShoppingCart size={20} className="text-gray-400" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-gray-900 truncate">{product.name}</p>
              <p className="text-xs text-gray-500">
                {product.category} · {product.shelf_location}
              </p>
              {product.price !== null && product.price !== undefined && (
                <p className="text-blue-600 font-semibold text-sm">{formatMoney(product.price)}</p>
              )}
            </div>
            {product.in_stock && (
              <span className="px-2 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium whitespace-nowrap">
                Còn {product.stock}
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onOpenMap?.(store) || window.open(store.map_url, '_blank')}
            className="flex-1 px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 flex items-center justify-center gap-1"
          >
            <Navigation className="w-3.5 h-3.5" /> Chỉ đường
          </button>
          <button
            onClick={() => onOpenStore?.() || navigate(`/store/${store.id}`)}
            className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 flex items-center justify-center gap-1"
          >
            <Store className="w-3.5 h-3.5" /> Vào shop
          </button>
          {product && onAddToCart && (
            <button
              onClick={() => onAddToCart(store.id, product.id)}
              className="flex-1 px-3 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium hover:bg-orange-600 flex items-center justify-center gap-1"
            >
              <ShoppingCart className="w-3.5 h-3.5" /> Thêm
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
