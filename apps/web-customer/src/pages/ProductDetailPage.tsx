import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShoppingCart, Heart, Share2, Store } from 'lucide-react';
import { apiService } from '../services/api';

interface Product {
  id: string;
  name: string;
  description?: string;
  price?: number;
  stock?: number;
  unit?: string;
  weight_grams?: number;
  barcode?: string;
  brand?: string;
  images?: string[];
  shelf_location?: string;
  category_name?: string;
  status?: string;
  store: {
    id: string;
    name: string;
    address: string;
    latitude: number;
    longitude: number;
  };
}

interface Alternative {
  id: string;
  name: string;
  price?: number;
  stock?: number;
  store_name?: string;
}

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [alternatives, setAlternatives] = useState<Alternative[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    if (id) loadProduct(id);
  }, [id]);

  const loadProduct = async (productId: string) => {
    try {
      const [productRes, altRes] = await Promise.all([
        apiService.get(`/products/${productId}`),
        apiService.get(`/products/${productId}/alternatives?limit=5`),
      ]);
      setProduct(productRes.data);
      setAlternatives(altRes.data.alternatives || []);
    } catch (err) {
      console.error('Failed to load product:', err);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async () => {
    if (!product) return;
    try {
      await apiService.post('/cart/items', { product_id: product.id, quantity });
      alert('Da them vao gio hang!');
    } catch (err) {
      const cart = JSON.parse(localStorage.getItem('cart') || '[]');
      cart.push({
        id: `temp-${Date.now()}`,
        product: { name: product.name, price: product.price, unit: product.unit, images: product.images },
        quantity,
        unit_price: product.price || 0,
        subtotal: (product.price || 0) * quantity,
      });
      localStorage.setItem('cart', JSON.stringify(cart));
      alert('Da them vao gio hang!');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-lg mx-auto p-4 text-center">
        <p className="text-gray-500">Không tim thay san pham</p>
        <button onClick={() => navigate('/')} className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg">
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto pb-24">
      {/* Image Gallery */}
      <div className="relative h-72 bg-gray-100">
        {product.images?.[0] ? (
          <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-8xl">📦</div>
        )}
        <button
          onClick={() => navigate(-1)}
          className="absolute top-4 left-4 p-2 bg-white rounded-full shadow-lg"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
      </div>

      {/* Product Info */}
      <div className="p-4 bg-white">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold">{product.name}</h1>
            {product.brand && <p className="text-gray-500">{product.brand}</p>}
          </div>
          <div className="flex gap-2">
            <button className="p-2 bg-gray-100 rounded-full"><Heart className="w-5 h-5" /></button>
            <button className="p-2 bg-gray-100 rounded-full"><Share2 className="w-5 h-5" /></button>
          </div>
        </div>

        <div className="mt-3">
          <span className="text-3xl font-bold text-blue-600">
            {product.price?.toLocaleString('vi-VN')}đ
          </span>
          <span className="text-gray-500 ml-2">/ {product.unit || 'cai'}</span>
        </div>

        {product.stock !== undefined && (
          <p className={`mt-2 text-sm ${product.stock > 0 ? 'text-green-600' : 'text-red-500'}`}>
            {product.stock > 0 ? `Còn hàng: ${product.stock}` : 'Hết hàng'}
          </p>
        )}

        {product.shelf_location && (
          <p className="mt-1 text-sm text-gray-500">📍 Vi tri: {product.shelf_location}</p>
        )}

        {/* Quantity Selector */}
        <div className="flex items-center gap-3 mt-4">
          <span className="font-medium">So luong:</span>
          <div className="flex items-center border rounded-lg">
            <button
              onClick={() => setQuantity(Math.max(1, quantity - 1))}
              className="px-3 py-2 border-r hover:bg-gray-50"
            >
              -
            </button>
            <span className="px-4 py-2 min-w-[3rem] text-center">{quantity}</span>
            <button
              onClick={() => setQuantity(quantity + 1)}
              className="px-3 py-2 border-l hover:bg-gray-50"
            >
              +
            </button>
          </div>
        </div>

        {/* Store Info */}
        <div className="mt-4 p-3 bg-gray-50 rounded-xl">
          <Link to={`/store/${product.store.id}`} className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Store className="w-5 h-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="font-medium">{product.store.name}</p>
              <p className="text-sm text-gray-500">{product.store.address}</p>
            </div>
            <span className="text-blue-600 text-sm">Xem cua hang →</span>
          </Link>
        </div>

        {/* Description */}
        {product.description && (
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Mo ta</h3>
            <p className="text-gray-600 text-sm leading-relaxed">{product.description}</p>
          </div>
        )}

        {/* Alternatives */}
        {alternatives.length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold mb-3">Sản phẩm tuong tu</h3>
            <div className="space-y-2">
              {alternatives.map((alt) => (
                <Link
                  key={alt.id}
                  to={`/product/${alt.id}`}
                  className="flex justify-between items-center p-3 bg-white border rounded-xl hover:bg-gray-50"
                >
                  <div>
                    <p className="font-medium">{alt.name}</p>
                    <p className="text-sm text-gray-500">{alt.store_name}</p>
                  </div>
                  <span className="text-blue-600 font-medium">{alt.price?.toLocaleString('vi-VN')}đ</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4">
        <div className="max-w-lg mx-auto flex gap-3">
          <button
            onClick={addToCart}
            className="flex-1 py-3 bg-blue-100 text-blue-700 rounded-xl font-medium hover:bg-blue-200 flex items-center justify-center gap-2"
          >
            <ShoppingCart className="w-5 h-5" /> Thêm vào gio
          </button>
          <button
            onClick={addToCart}
            className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700"
          >
            Mua ngay
          </button>
        </div>
      </div>
    </div>
  );
}
