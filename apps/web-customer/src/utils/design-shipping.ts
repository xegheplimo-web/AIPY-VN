export function calculateShippingFee(distanceKm: number, weightGrams: number, orderValue: number) {
  if (orderValue >= 300000) return 0;
  let baseFee = 15000;
  if (distanceKm > 2 && distanceKm <= 5) baseFee = 25000;
  if (distanceKm > 5 && distanceKm <= 10) baseFee = 40000;
  if (distanceKm > 10) baseFee = 40000 + Math.ceil((distanceKm - 10) / 2) * 10000;
  const extraKgFee = weightGrams > 1000 ? Math.ceil((weightGrams - 1000) / 1000) * 5000 : 0;
  return baseFee + extraKgFee;
}
