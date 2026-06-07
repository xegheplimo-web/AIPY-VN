export type Product = {
  id: string;
  name: string;
  category: string;
  price: number;
  oldPrice?: number;
  stock: number;
  unit: string;
  shelfLocation?: string;
  image: string;
  rating?: number;
  sold?: number;
  description?: string;
};

export type Store = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  distanceKm: number;
  industry: string;
  coverImage: string;
  logo: string;
  phone: string;
  zalo: string;
  rating: number;
  reviews: number;
  isOpenNow: boolean;
  products: Product[];
};

export type CartItem = {
  storeId: string;
  productId: string;
  quantity: number;
};

export type OrderStatus = 'ordered' | 'confirmed' | 'preparing' | 'shipping' | 'done';
