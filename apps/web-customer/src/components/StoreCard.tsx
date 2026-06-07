import { MapPin, Phone, MessageCircle } from 'lucide-react';

interface StoreCardProps {
  store: any;
  userLocation?: any;
}

export default function StoreCard({ store, userLocation }: StoreCardProps) {
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371e3;
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const deltaPhi = (lat2 - lat1) * Math.PI / 180;
    const deltaLambda = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(deltaPhi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  };

  const distance = userLocation
    ? calculateDistance(userLocation.lat, userLocation.lng, store.latitude, store.longitude)
    : null;

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
      <div className="relative h-48 bg-gray-200">
        {store.cover_image_url ? (
          <img src={store.cover_image_url} alt={store.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            🏪 Chưa có ảnh
          </div>
        )}
        <div className="absolute top-4 right-4 bg-white px-3 py-1 rounded-full shadow">
          {store.is_open_now ? (
            <span className="text-green-600 text-sm font-medium">● Đang mở</span>
          ) : (
            <span className="text-red-600 text-sm font-medium">● Đã đóng</span>
          )}
        </div>
        {distance && (
          <div className="absolute top-4 left-4 bg-blue-600 text-white px-3 py-1 rounded-full shadow">
            📍 {(distance / 1000).toFixed(1)}km
          </div>
        )}
      </div>

      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{store.name}</h3>
            <p className="text-sm text-gray-500 mt-1 flex items-center">
              <MapPin className="w-4 h-4 mr-1" />
              {store.address}
            </p>
            {store.rating > 0 && (
              <div className="flex items-center mt-2">
                <span className="text-yellow-500">★</span>
                <span className="ml-1 text-sm font-medium">{store.rating}</span>
                <span className="ml-1 text-sm text-gray-400">({store.total_reviews} đánh giá)</span>
              </div>
            )}
          </div>
          {store.logo_url && (
            <img src={store.logo_url} alt="Logo" className="w-16 h-16 rounded-full border-2 border-white shadow" />
          )}
        </div>

        <div className="mt-4 space-y-3">
          <h4 className="font-semibold text-gray-700">Sản phẩm tìm thấy:</h4>
          {store.products.map((product: any) => (
            <div key={product.id} className="flex gap-4 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition">
              <div className="w-20 h-20 bg-white rounded-lg flex items-center justify-center flex-shrink-0">
                {product.images?.[0] ? (
                  <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover rounded-lg" />
                ) : (
                  <span className="text-3xl">📦</span>
                )}
              </div>
              <div className="flex-1">
                <h5 className="font-medium text-gray-900">{product.name}</h5>
                <p className="text-sm text-gray-500">{product.category}</p>
                <div className="flex items-center justify-between mt-2">
                  <div>
                    <span className="text-lg font-bold text-blue-600">
                      {product.price?.toLocaleString('vi-VN')}đ
                    </span>
                    <span className="text-xs text-gray-400 ml-2">/ {product.unit || 'cái'}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded ${
                    product.stock > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {product.stock > 0 ? `Còn ${product.stock}` : 'Hết hàng'}
                  </span>
                </div>
                {product.shelf_location && (
                  <p className="text-xs text-gray-400 mt-1">📍 {product.shelf_location}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 grid grid-cols-3 gap-3">
          <button
            onClick={() => window.open(store.map_url, '_blank')}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition"
          >
            <MapPin className="w-4 h-4" />
            Chỉ đường
          </button>
          <button
            onClick={() => window.location.href = `/store/${store.id}`}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition"
          >
            🏪 Vào cửa hàng
          </button>
          <button
            onClick={() => window.location.href = `/chat?store_id=${store.id}`}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition"
          >
            <MessageCircle className="w-4 h-4" />
            Chat
          </button>
        </div>
      </div>
    </div>
  );
}
