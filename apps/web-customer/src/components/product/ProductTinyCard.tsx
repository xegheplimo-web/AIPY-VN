import { ShoppingCart } from 'lucide-react';
import type { Product } from '../../types/design';
import { money } from '../../utils/design-format';

interface ProductTinyCardProps {
  product: Product;
  onClick?: (product: Product) => void;
}

export default function ProductTinyCard({ product, onClick }: ProductTinyCardProps) {
  return (
    <div
      onClick={() => onClick?.(product)}
      className="bg-white rounded-xl border border-gray-200 p-3 cursor-pointer hover:shadow-md transition"
    >
      <div className="aspect-square bg-gray-100 rounded-lg mb-2 flex items-center justify-center">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-cover rounded-lg"
          />
        ) : (
          <ShoppingCart size={24} className="text-gray-400" />
        )}
      </div>
      <h4 className="font-medium text-sm text-gray-900 truncate">{product.name}</h4>
      <p className="text-blue-600 font-semibold text-sm mt-1">{money(product.price)}</p>
      {product.stock > 0 && (
        <span className="text-xs text-green-600 mt-1">Còn {product.stock}</span>
      )}
    </div>
  );
}
