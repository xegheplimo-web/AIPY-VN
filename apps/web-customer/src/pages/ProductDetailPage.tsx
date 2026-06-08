import { ArrowLeft, Heart, MapPin, Minus, Plus, Share2, ShoppingCart, Store } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { Product } from '../services/api';
import { apiService } from '../services/api';

interface ProductOffer {
  store_id: string;
  store_name: string;
  distance_m: number;
  price: number;
  stock: number;
  is_open_now: boolean;
  map_url: string;
}

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [offers, setOffers] = useState<ProductOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);
  const [favLoading, setFavLoading] = useState(false);

  useEffect(() => {
    if (id) loadProduct(id);
  }, [id]);

  const loadProduct = async (productId: string) => {
    try {
      setLoading(true);
      const productData = await apiService.getProduct(productId);
      setProduct(productData);

      // Try to load multi-store offers if available
      try {
        const offersData = await apiService.getProductOffers(productId);
        setOffers(offersData.offers || []);
      } catch {
        // Backend may not support /offers yet; fallback to store from product
        if (productData.store) {
          setOffers([
            {
              store_id: productData.store_id,
              store_name: productData.store.name,
              distance_m: productData.store.distance_m || 0,
              price: productData.price || 0,
              stock: productData.stock,
              is_open_now: productData.store.is_open_now,
              map_url: `https://www.google.com/maps/dir/?api=1&destination=${productData.store.latitude},${productData.store.longitude}&q=${encodeURIComponent(productData.store.name)}`,
            },
          ]);
        }
      }
    } catch (err) {
      console.error('Failed to load product:', err);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async () => {
    if (!product) return;
    try {
      setAdding(true);
      await apiService.addToCart(product.id, quantity);
      alert('Đã thêm vào giỏ hàng!');
    } catch (err) {
      console.error('Failed to add to cart:', err);
      // Fallback localStorage with store_id
      const cart = JSON.parse(localStorage.getItem('cart') || '[]');
      const existing = cart.find((item: any) => item.product_id === product.id);
      if (existing) {
        existing.quantity += quantity;
      } else {
        cart.push({
          id: `local-${Date.now()}`,
          product_id: product.id,
          name: product.name,
          price: product.price || 0,
          quantity,
          stock: product.stock,
          store_id: product.store_id,
          store_name: product.store?.name || '',
          store: {
            id: product.store_id,
            name: product.store?.name || '',
            address: product.store?.address || '',
            distanceKm: product.store?.distance_m ? product.store.distance_m / 1000 : 0,
            isSameDistrict: true,
          },
          images: product.images,
          unit: product.unit || 'cái',
          subtotal: (product.price || 0) * quantity,
        });
      }
      localStorage.setItem('cart', JSON.stringify(cart));
      alert('Đã thêm vào giỏ hàng (local)!');
    } finally {
      setAdding(false);
    }
  };

  const buyNow = async () => {
    await addToCart();
    navigate('/cart');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-lg mx-auto p-4 text-center">
        <p className="text-gray-500">Không tìm thấy sản phẩm</p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg"
        >
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto pb-28">
      {/* Image Gallery */}
      <div className="relative h-72 bg-gray-100">
        {product.images?.[0] ? (
          <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-8xl">
            📦
          </div>
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
          <div className="flex-1">
            <h1 className="text-xl font-bold">{product.name}</h1>
            {product.category && <p className="text-gray-500 text-sm">{product.category}</p>}
          </div>
          <div className="flex gap-2">
            <button
              onClick={async () => {
                if (!product || favLoading) return;
                setFavLoading(true);
                try {
                  if (isFavorite) {
                    await apiService.removeFavorite(product.id);
                    setIsFavorite(false);
                  } else {
                    await apiService.addFavorite(product.id);
                    setIsFavorite(true);
                  }
                } catch (err) {
                  console.error('Favorite toggle failed:', err);
                } finally {
                  setFavLoading(false);
                }
              }}
              disabled={favLoading}
              className="p-2 bg-gray-100 rounded-full hover:bg-red-50 disabled:opacity-50"
            >
              <Heart className={"w-5 h-5 " + (isFavorite ? 'text-red-500 fill-red-500' : 'text-gray-600')} />
            </button>
            <button className="p-2 bg-gray-100 rounded-full">
              <Share2 className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="mt-3">
          <span className="text-3xl font-bold text-blue-600">
            {product.price?.toLocaleString('vi-VN')}đ
          </span>
          <span className="text-gray-500 ml-2">/ {product.unit || 'cái'}</span>
        </div>

        {product.stock !== undefined && (
          <p className={`mt-2 text-sm ${product.stock > 0 ? 'text-green-600' : 'text-red-500'}`}>
            {product.stock > 0 ? `Còn hàng: ${product.stock}` : 'Hết hàng'}
          </p>
        )}

        {product.shelf_location && (
          <p className="mt-1 text-sm text-gray-500">📍 Vị trí: {product.shelf_location}</p>
        )}

        {/* Quantity Selector */}
        <div className="flex items-center gap-3 mt-4">
          <span className="font-medium">Số lượng:</span>
          <div className="flex items-center border rounded-lg">
            <button
              onClick={() => setQuantity(Math.max(1, quantity - 1))}
              className="px-3 py-2 border-r hover:bg-gray-50"
            >
              <Minus className="w-4 h-4" />
            </button>
            <span className="px-4 py-2 min-w-[3rem] text-center">{quantity}</span>
            <button
              onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
              disabled={quantity >= product.stock}
              className="px-3 py-2 border-l hover:bg-gray-50 disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Store Info */}
        {product.store && (
          <div className="mt-4 p-3 bg-gray-50 rounded-xl">
            <Link to={`/store/${product.store.id}`} className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Store className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="font-medium">{product.store.name}</p>
                <p className="text-sm text-gray-500">{product.store.address}</p>
              </div>
              <span className="text-blue-600 text-sm">Xem cửa hàng →</span>
            </Link>
          </div>
        )}

        {/* Description */}
        {product.description && (
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Mô tả</h3>
            <p className="text-gray-600 text-sm leading-relaxed">{product.description}</p>
          </div>
        )}

        {/* Multi-store Offers */}
        {offers.length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold mb-3">Cửa hàng có bán gần bạn</h3>
            <div className="space-y-2">
              {offers.map((offer) => (
                <div
                  key={offer.store_id}
                  className="flex items-center gap-3 p-3 bg-white border rounded-xl hover:bg-gray-50"
                >
                  <Store className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-sm">{offer.store_name}</p>
                    <p className="text-xs text-gray-500">
                      {offer.distance_m < 1000
                        ? `${offer.distance_m}m`
                        : `${(offer.distance_m / 1000).toFixed(1)}km`}{' '}
                      · Còn {offer.stock}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-blue-600 font-bold text-sm">
                      {offer.price.toLocaleString('vi-VN')}đ
                    </p>
                    {offer.is_open_now ? (
                      <span className="text-xs text-green-600">Đang mở</span>
                    ) : (
                      <span className="text-xs text-red-500">Đã đóng</span>
                    )}
                  </div>
                  <a
                    href={offer.map_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100"
                  >
                    <MapPin className="w-4 h-4" />
                  </a>
                </div>
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
            disabled={adding || product.stock <= 0}
            className="flex-1 py-3 bg-blue-100 text-blue-700 rounded-xl font-medium hover:bg-blue-200 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <ShoppingCart className="w-5 h-5" /> Thêm vào giỏ
          </button>
          <button
            onClick={buyNow}
            disabled={adding || product.stock <= 0}
            className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            Mua ngay
          </button>
        </div>
      </div>
    </div>
  );
}
