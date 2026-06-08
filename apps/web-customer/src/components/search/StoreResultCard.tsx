import { MapPin, Store as StoreIcon } from 'lucide-react';
import type { Product, Store } from '../../types/design';
import { money, km } from '../../utils/design-format';

interface StoreResultCardProps {
  store: Store;
  product?: Product;
  onOpenMap?: (store: Store) => void;
  onOpenStore?: (store: Store) => void;
  onAddToCart?: (storeId: string, productId: string) => void;
  onOpenProduct?: (product: Product) => void;
}

export default function StoreResultCard({
  store,
  product,
  onOpenMap,
  onOpenStore,
  onAddToCart,
  onOpenProduct,
}: StoreResultCardProps) {
  const displayProduct = product || store.products[0];

  return (
    <article className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-3">
      {/* Store Cover */}
      {store.coverImage && (
        <img
          className="w-full h-32 object-cover"
          src={store.coverImage}
          alt={store.name}
        />
      )}

      {/* Store Info */}
      <div className="p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">{store.name}</h4>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
              <MapPin size={13} /> {store.address}
            </p>
          </div>
          <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
            {km(store.distanceKm)}
          </span>
        </div>

        {/* Product Info */}
        {displayProduct && (
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mb-3">
            {displayProduct.image && (
              <img
                className="w-16 h-16 object-cover rounded-lg"
                src={displayProduct.image}
                alt={displayProduct.name}
              />
            )}
            <div className="flex-1">
              <p className="font-medium text-gray-900">{displayProduct.name}</p>
              <p className="text-xs text-gray-500 mt-1">
                {displayProduct.category} · {displayProduct.shelfLocation}
              </p>
              <p className="font-bold text-blue-600 mt-1">{money(displayProduct.price)}</p>
            </div>
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
              Còn {displayProduct.stock}
            </span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-4 gap-2">
          <button
            onClick={() => onOpenMap?.(store)}
            className="py-2 text-sm bg-green-50 text-green-700 rounded-lg hover:bg-green-100 font-medium"
          >
            Chỉ đường
          </button>
          <button
            onClick={() => onOpenStore?.(store)}
            className="py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 font-medium"
          >
            Vào cửa hàng
          </button>
          {displayProduct && onAddToCart && (
            <button
              onClick={() => onAddToCart(store.id, displayProduct.id)}
              className="py-2 text-sm bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 font-medium"
            >
              Thêm
            </button>
          )}
          {displayProduct && onOpenProduct && (
            <button
              onClick={() => onOpenProduct(displayProduct)}
              className="py-2 text-sm bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 font-medium"
            >
              Chi tiết
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
