import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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
  distance?: {
    meters: number;
    text: string;
  };
  opening_hours?: any;
}

interface InteractiveMapProps {
  stores: Store[];
  center?: [number, number];
  zoom?: number;
  onStoreClick?: (store: Store) => void;
  userLocation?: [number, number];
  radius?: number;
}

function MapController({ center, zoom }: { center?: [number, number]; zoom?: number }) {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.setView(center, zoom || 13);
    }
  }, [center, zoom, map]);

  return null;
}

function RadiusCircle({ center, radius }: { center: [number, number]; radius: number }) {
  const map = useMap();

  useEffect(() => {
    if (center && radius) {
      const circle = L.circle(center, {
        radius: radius * 1000, // Convert km to meters
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.1,
        weight: 2,
      }).addTo(map);

      return () => {
        map.removeLayer(circle);
      };
    }
  }, [center, radius, map]);

  return null;
}

export default function InteractiveMap({
  stores,
  center = [10.7769, 106.7009], // Default: Ho Chi Minh City
  zoom = 13,
  onStoreClick,
  userLocation,
  radius,
}: InteractiveMapProps) {
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);

  const handleMarkerClick = (store: Store) => {
    setSelectedStore(store);
    onStoreClick?.(store);
  };

  return (
    <div className="w-full h-full rounded-xl overflow-hidden border border-gray-200">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapController center={center} zoom={zoom} />

        {userLocation && (
          <Marker
            position={userLocation}
            icon={L.divIcon({
              className: 'user-location-marker',
              html: `<div style="
                background-color: #3b82f6;
                border: 3px solid white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
              "></div>`,
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            })}
          >
            <Popup>Vị trí của bạn</Popup>
          </Marker>
        )}

        {radius && userLocation && <RadiusCircle center={userLocation} radius={radius} />}

        {stores.map((store) => (
          <Marker
            key={store.id}
            position={[store.lat, store.lng]}
            eventHandlers={{
              click: () => handleMarkerClick(store),
            }}
          >
            <Popup>
              <div className="p-2 min-w-[200px]">
                <h3 className="font-semibold text-gray-900 mb-1">{store.name}</h3>
                {store.category && (
                  <div className="flex items-center gap-1 text-sm text-gray-600 mb-1">
                    <span>{store.category.icon}</span>
                    <span>{store.category.name}</span>
                  </div>
                )}
                {store.distance && (
                  <div className="text-sm text-blue-600 font-medium mb-1">
                    {store.distance.text}
                  </div>
                )}
                <p className="text-sm text-gray-600 mb-2">{store.address}</p>
                {store.phone && (
                  <a
                    href={`tel:${store.phone}`}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    📞 {store.phone}
                  </a>
                )}
                {store.rating && (
                  <div className="flex items-center gap-1 mt-2">
                    <span className="text-yellow-500">⭐</span>
                    <span className="text-sm font-medium">{store.rating}</span>
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
