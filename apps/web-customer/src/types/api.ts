// API Response Types
export interface SearchProductResult {
  id: string;
  name: string;
  price: number | null;
  stock: number;
  in_stock: boolean;
  shelf_location: string;
  category: string | null;
}

export interface SearchStoreResult {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  distance_m: number | null;
  logo_url: string | null;
  cover_image_url: string | null;
  rating: number | null;
  total_reviews: number | null;
  is_open_now: boolean | null;
  industry: string | null;
  map_url: string;
  products: SearchProductResult[];
}

export interface ChatSearchResponse {
  summary: string;
  stores: SearchStoreResult[];
  total_found: number;
}

export interface ChatSearchRequest {
  query: string;
  location?: {
    lat: number;
    lng: number;
  };
  radius_km: number;
  limit: number;
}

export interface Store {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  phone: string | null;
  email: string | null;
  zalo: string | null;
  logo_url: string | null;
  cover_image_url: string | null;
  business_hours: Record<string, any> | null;
  rating: number | null;
  review_count: number | null;
  is_open_now: boolean;
  industry: string | null;
  distance_m?: number;
}

export interface Product {
  id: string;
  name: string;
  price: number | null;
  stock: number;
  shelf_location: string;
  category: string | null;
  store_id: string;
  store?: Store;
  images: string[];
  description: string | null;
}

export interface CartItem {
  product: Product;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: string;
  user_id: string;
  store_id: string;
  status: string;
  total_amount: number;
  shipping_fee: number;
  delivery_method: 'pickup' | 'delivery';
  created_at: string;
  items: OrderItem[];
}

export interface OrderItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  phone: string | null;
  addresses: Address[];
}

export interface Address {
  id: string;
  full_address: string;
  latitude: number;
  longitude: number;
  is_default: boolean;
}
