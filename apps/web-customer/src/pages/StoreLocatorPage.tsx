import { useState, useEffect } from 'react';
import { MapPin, Navigation, Filter, X, Star, Clock, Phone } from 'lucide-react';
import InteractiveMap from '../components/InteractiveMap';
import GeoAutocomplete from '../components/GeoAutocomplete';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';

interface Store {
  id: string;
  name: string;
  lat: number;
  lng: number;
  address: string;
  phone?: string;
  category?: {
    name: string;
    icon: string;
  };
  brand?: {
    name: string;
    logo?: string;
  };
  rating?: number;
  review_count?: number;
  distance?: {
    meters: number;
    text: string;
  };
  opening_hours?: any;
  images?: string[];
}

interface Category {
  id: number;
  name_vi: string;
  icon: string;
  slug: string;
}

interface Brand {
  id: number;
  name: string;
  slug: string;
  logo_url?: string;
}

export default function StoreLocatorPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [radius, setRadius] = useState(5);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');

  // Get user location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLocation([pos.coords.latitude, pos.coords.longitude]);
        },
        (err) => {
          console.warn('Không lấy được GPS:', err);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }
  }, []);

  // Load categories
  useEffect(() => {
    fetch('/api/geo/categories')
      .then((res) => res.json())
      .then((data) => setCategories(data))
      .catch((err) => console.error('Failed to load categories:', err));
  }, []);

  // Load brands
  useEffect(() => {
    fetch('/api/geo/brands')
      .then((res) => res.json())
      .then((data) => setBrands(data))
      .catch((err) => console.error('Failed to load brands:', err));
  }, []);

  // Search nearby stores
  const searchNearby = async () => {
    if (!userLocation) {
      alert('Vui lòng cho phép truy cập vị trí GPS');
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        lat: userLocation[0].toString(),
        lng: userLocation[1].toString(),
        radius: radius.toString(),
      });

      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedBrand) params.append('brand', selectedBrand);

      const response = await fetch(`/api/geo/nearby?${params}`);
      const data = await response.json();
      setStores(data.stores || []);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Search by text
  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ q: query });
      if (userLocation) {
        params.append('lat', userLocation[0].toString());
        params.append('lng', userLocation[1].toString());
      }
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedBrand) params.append('brand', selectedBrand);

      const response = await fetch(`/api/geo/search?${params}`);
      const data = await response.json();
      setStores(data.stores || []);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get current location
  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLocation([pos.coords.latitude, pos.coords.longitude]);
          searchNearby();
        },
        (err) => {
          alert('Không lấy được vị trí GPS');
        }
      );
    }
  };

  // Clear filters
  const clearFilters = () => {
    setSelectedCategory(null);
    setSelectedBrand(null);
    setRadius(5);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <h1 className="text-2xl font-bold text-blue-600">VietStore</h1>
            <div className="flex-1 max-w-2xl">
              <GeoAutocomplete
                onSearch={handleSearch}
                location={userLocation ? { lat: userLocation[0], lng: userLocation[1] } : undefined}
              />
            </div>
            <Button
              onClick={getCurrentLocation}
              className="flex items-center gap-2"
            >
              <Navigation className="h-4 w-4" />
              Gần tôi
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* Sidebar */}
          <aside className="w-80 flex-shrink-0">
            <Card className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-lg">Bộ lọc</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFilters(!showFilters)}
                >
                  <Filter className="h-4 w-4" />
                </Button>
              </div>

              {showFilters && (
                <div className="space-y-4">
                  {/* Radius */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Bán kính</label>
                    <select
                      value={radius}
                      onChange={(e) => setRadius(Number(e.target.value))}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value={1}>1 km</option>
                      <option value={2}>2 km</option>
                      <option value={5}>5 km</option>
                      <option value={10}>10 km</option>
                      <option value={20}>20 km</option>
                    </select>
                  </div>

                  {/* Categories */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Danh mục</label>
                    <ScrollArea className="h-40">
                      <div className="space-y-1">
                        <button
                          onClick={() => setSelectedCategory(null)}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                            !selectedCategory ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
                          }`}
                        >
                          Tất cả
                        </button>
                        {categories.map((cat) => (
                          <button
                            key={cat.id}
                            onClick={() => setSelectedCategory(cat.slug)}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 ${
                              selectedCategory === cat.slug ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
                            }`}
                          >
                            <span>{cat.icon}</span>
                            <span>{cat.name_vi}</span>
                          </button>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>

                  {/* Brands */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Thương hiệu</label>
                    <ScrollArea className="h-40">
                      <div className="space-y-1">
                        <button
                          onClick={() => setSelectedBrand(null)}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                            !selectedBrand ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
                          }`}
                        >
                          Tất cả
                        </button>
                        {brands.map((brand) => (
                          <button
                            key={brand.id}
                            onClick={() => setSelectedBrand(brand.slug)}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                              selectedBrand === brand.slug ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
                            }`}
                          >
                            {brand.name}
                          </button>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button onClick={searchNearby} className="flex-1">
                      Tìm kiếm
                    </Button>
                    <Button variant="outline" onClick={clearFilters}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}

              {/* View Toggle */}
              <div className="flex gap-2 mt-4">
                <Button
                  variant={viewMode === 'map' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('map')}
                  className="flex-1"
                >
                  Bản đồ
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="flex-1"
                >
                  Danh sách
                </Button>
              </div>
            </Card>

            {/* Store List */}
            {viewMode === 'list' && (
              <Card className="mt-4 p-4">
                <ScrollArea className="h-[calc(100vh-400px)]">
                  <div className="space-y-3">
                    {stores.map((store) => (
                      <div
                        key={store.id}
                        onClick={() => setSelectedStore(store)}
                        className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          {store.category?.icon && (
                            <span className="text-2xl">{store.category.icon}</span>
                          )}
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-gray-900">{store.name}</h3>
                            {store.brand && (
                              <Badge variant="secondary" className="mt-1">
                                {store.brand.name}
                              </Badge>
                            )}
                            <p className="text-sm text-gray-600 mt-1">{store.address}</p>
                            {store.distance && (
                              <div className="text-sm text-blue-600 mt-1">{store.distance.text}</div>
                            )}
                            {store.rating && (
                              <div className="flex items-center gap-1 mt-1">
                                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                                <span className="text-sm">{store.rating}</span>
                                {store.review_count && (
                                  <span className="text-sm text-gray-500">({store.review_count})</span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    {stores.length === 0 && !loading && (
                      <div className="text-center py-8 text-gray-500">
                        Không tìm thấy cửa hàng nào
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </Card>
            )}
          </aside>

          {/* Map */}
          <main className="flex-1">
            <Card className="overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
              {viewMode === 'map' ? (
                <InteractiveMap
                  stores={stores}
                  center={userLocation || undefined}
                  userLocation={userLocation || undefined}
                  radius={radius}
                  onStoreClick={setSelectedStore}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500">
                  Chọn chế độ bản đồ để xem
                </div>
              )}
            </Card>
          </main>
        </div>
      </div>

      {/* Store Detail Dialog */}
      <Dialog open={!!selectedStore} onOpenChange={() => setSelectedStore(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {selectedStore?.category?.icon && (
                <span className="text-3xl">{selectedStore.category.icon}</span>
              )}
              {selectedStore?.name}
            </DialogTitle>
          </DialogHeader>
          {selectedStore && (
            <div className="space-y-4">
              {selectedStore.brand && (
                <Badge variant="secondary">{selectedStore.brand.name}</Badge>
              )}
              
              <div className="flex items-start gap-2 text-gray-600">
                <MapPin className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <p>{selectedStore.address}</p>
              </div>

              {selectedStore.distance && (
                <div className="flex items-center gap-2 text-blue-600">
                  <Navigation className="h-5 w-5" />
                  <span className="font-medium">{selectedStore.distance.text}</span>
                </div>
              )}

              {selectedStore.phone && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Phone className="h-5 w-5" />
                  <a href={`tel:${selectedStore.phone}`} className="hover:text-blue-600">
                    {selectedStore.phone}
                  </a>
                </div>
              )}

              {selectedStore.rating && (
                <div className="flex items-center gap-2">
                  <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
                  <span className="font-medium">{selectedStore.rating}</span>
                  {selectedStore.review_count && (
                    <span className="text-gray-500">({selectedStore.review_count} đánh giá)</span>
                  )}
                </div>
              )}

              {selectedStore.opening_hours && (
                <div className="flex items-start gap-2 text-gray-600">
                  <Clock className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Giờ mở cửa</p>
                    <p className="text-sm">{selectedStore.opening_hours.raw || 'Liên hệ cửa hàng'}</p>
                  </div>
                </div>
              )}

              {selectedStore.images && selectedStore.images.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {selectedStore.images.map((img, idx) => (
                    <img
                      key={idx}
                      src={img}
                      alt={`${selectedStore.name} ${idx + 1}`}
                      className="rounded-lg w-full h-24 object-cover"
                    />
                  ))}
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button className="flex-1">Chỉ đường</Button>
                <Button variant="outline" className="flex-1">Gọi điện</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
