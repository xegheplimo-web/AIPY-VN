export function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth's radius in km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // Distance in km
}

function toRad(degrees: number): number {
  return degrees * (Math.PI / 180);
}

export function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
}

export function calculateShippingFee(distanceKm: number, weightKg: number = 0, subtotal: number = 0): number {
  // Free shipping for orders over 300k
  if (subtotal >= 300000) {
    return 0;
  }

  // Base shipping fee by distance
  let baseFee = 0;
  if (distanceKm <= 2) {
    baseFee = 15000;
  } else if (distanceKm <= 5) {
    baseFee = 25000;
  } else if (distanceKm <= 10) {
    baseFee = 40000;
  } else {
    baseFee = 40000 + Math.ceil((distanceKm - 10) / 2) * 10000;
  }

  // Additional fee for heavy items
  const weightFee = weightKg > 1 ? Math.ceil(weightKg - 1) * 5000 : 0;

  return baseFee + weightFee;
}
