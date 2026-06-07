import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Phone, MessageCircle, Star, Clock } from 'lucide-react';
import api from '../services/api';

interface Store {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  phone?: string;
  email?: string;
  zalo?: string;
  logo_url?: string;
  cover_image_url?: string;
  business_hours?: Record<string, string>;
  is_open_now?: boolean;
  rating?: number;
  total_reviews?: number;
  industry?: string;
  products_count?: number;
  average_rating?: number;
}

interface Product {
  id: string;
  name: string;
  description?: string;
  price?: number;
  stock: number;
  unit: string;
  images?: string[];
  shelf_location?: string;
}

export default function StoreDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [store, setStore] = useState<Store | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) loadStoreDetail(id);
  }, [id]);

  const loadStoreDetail = async (storeId: string) => {
    try {
      const [storeRes, productsRes] = await Promise.all([
        api.get(`/stores/${storeId}`),
        api.get(`/stores/${storeId}/products?limit=20`),
      ]);
      setStore(storeRes.data);
      setProducts(productsRes.data.products || []);
    } catch (err) {
      console.error('Failed to load store detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (product: Product) => {
    try {
      await api.post('/cart/items', { product_id: product.id, quantity: 1 });
      alert('Da them vao gio hang!');
    } catch (err) {
      // Fallback to localStorage
      const cart = JSON.parse(localStorage.getItem('cart') || '[]');
      cart.push({
        id: `temp-${Date.now()}`,
        product: { name: product.name, price: product.price, unit: product.unit, images: product.images },
        quantity: 1,
        unit_price: product.price || 0,
        subtotal: product.price || 0,
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

  if (!store) {
    return (
      <div className="max-w-lg mx-auto p-4 text-center">
        <p className="text-gray-500">Khong tim thay cua hang</p>
        <button onClick={() => navigate('/')} className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg">
          Quay lai
        </button>
      </div>
    );
  }

  const mapUrl = `https://www.google.com/maps/dir/?api=1&destination=${store.latitude},${store.longitude}&q=${encodeURIComponent(store.name)}`;

  return (
    <div className="max-w-lg mx-auto pb-24">
      {/* Cover Image */}
      <div className="relative h-48 bg-gray-200">
        {store.cover_image_url ? (
          <img src={store.cover_image_url} alt={store.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-6xl">🏪</div>
        )}
        <button
          onClick={() => navigate(-1)}
          className="absolute top-4 left-4 p-2 bg-white rounded-full shadow-lg"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        {store.is_open_now !== undefined && (
          <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-sm font-medium ${store.is_open_now ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {store.is_open_now ? 'Dang mo' : 'Da dong'}
          </div>
        )}
      </div>

      {/* Store Info */}
      <div className="p-4 bg-white -mt-6 rounded-t-3xl relative">
        <div className="flex items-start gap-3">
          {store.logo_url && (
            <img src={store.logo_url} alt="" className="w-16 h-16 rounded-full border-2 border-white shadow -mt-10" />
          )}
          <div className="flex-1">
            <h1 className="text-xl font-bold">{store.name}</h1>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
              <MapPin className="w-4 h-4" /> {store.address}
            </p>
            {store.rating && (
              <div className="flex items-center gap-1 mt-1">
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                <span className="font-medium">{store.rating}</span>
                <span className="text-sm text-gray-400">({store.total_reviews || 0} danh gia)</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          <a href={mapUrl} target="_blank" rel="noopener noreferrer" className="flex flex-col items-center gap-1 p-3 bg-green-50 text-green-700 rounded-xl">
            <MapPin className="w-5 h-5" />
            <span className="text-sm font-medium">Chi duong</span>
          </a>
          <Link to={`/chat?store_id=${store.id}`} className="flex flex-col items-center gap-1 p-3 bg-purple-50 text-purple-700 rounded-xl">
            <MessageCircle className="w-5 h-5" />
            <span className="text-sm font-medium">Chat</span>
          </Link>
          {store.phone && (
            <a href={`tel:${store.phone}`} className="flex flex-col items-center gap-1 p-3 bg-blue-50 text-blue-700 rounded-xl">
              <Phone className="w-5 h-5" />
              <span className="text-sm font-medium">Goi dien</span>
            </a>
          )}
        </div>

        {/* Business Hours */}
        {store.business_hours && (
          <div className="mt-4 p-3 bg-gray-50 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="font-medium">Gio mo cua</span>
            </div>
            <div className="text-sm space-y-1">
              {Object.entries(store.business_hours).map(([day, hours]) => (
                <div key={day} className="flex justify-between">
                  <span className="capitalize text-gray-500">{day}</span>
                  <span>{hours}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Products */}
      <div className="p-4">
        <h2 className="text-lg font-bold mb-3">San pham ({products.length})</h2>
        <div className="space-y-3">
          {products.map((product) => (
            <div key={product.id} className="flex gap-3 p-3 bg-white rounded-xl shadow-sm border">
              <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                {product.images?.[0] ? (
                  <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover rounded-lg" />
                ) : (
                  <span className="text-2xl">📦</span>
                )}
              </div>
              <div className="flex-1">
                <Link to={`/product/${product.id}`} className="font-medium hover:text-blue-600">
                  {product.name}
                </Link>
                <p className="text-sm text-gray-500">{product.unit}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-blue-600 font-bold">{product.price?.toLocaleString('vi-VN')}đ</span>
                  <button
                    onClick={() => addToCart(product)}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                  >
                    Them
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
