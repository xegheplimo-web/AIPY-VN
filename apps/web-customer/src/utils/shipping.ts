/**
 * Tính phí ship theo khoảng cách, cân nặng, phương thức giao hàng
 * Công thức MVP:
 * - Nhận tại cửa hàng: 0đ
 * - Ship:
 *   - 0-2km: 15.000đ
 *   - 2-5km: 25.000đ
 *   - 5-10km: 40.000đ
 *   - >10km: 40.000đ + 10.000đ mỗi 2km
 * - Đơn từ 300.000đ: miễn phí ship nội quận
 * - Hàng >1kg: +5.000đ/kg
 */

export interface ShippingCalculationParams {
  distanceKm: number;
  weightKg: number;
  subtotal: number;
  deliveryMethod: 'pickup' | 'delivery';
  isSameDistrict: boolean;
}

export interface ShippingResult {
  fee: number;
  isFree: boolean;
  reason?: string;
}

export function calculateShippingFee(params: ShippingCalculationParams): ShippingResult {
  const { distanceKm, weightKg, subtotal, deliveryMethod, isSameDistrict } = params;

  // Nhận tại cửa hàng: miễn phí
  if (deliveryMethod === 'pickup') {
    return { fee: 0, isFree: true, reason: 'Nhận tại cửa hàng' };
  }

  // Đơn từ 300.000đ: miễn phí ship nội quận
  if (subtotal >= 300000 && isSameDistrict) {
    return { fee: 0, isFree: true, reason: 'Miễn phí ship (đơn ≥300.000đ)' };
  }

  // Tính phí theo khoảng cách
  let baseFee = 0;
  if (distanceKm <= 2) {
    baseFee = 15000;
  } else if (distanceKm <= 5) {
    baseFee = 25000;
  } else if (distanceKm <= 10) {
    baseFee = 40000;
  } else {
    // >10km: 40.000đ + 10.000đ mỗi 2km
    const extraKm = Math.ceil((distanceKm - 10) / 2);
    baseFee = 40000 + extraKm * 10000;
  }

  // Phí cho hàng nặng (>1kg)
  const weightFee = weightKg > 1 ? Math.ceil(weightKg - 1) * 5000 : 0;

  const totalFee = baseFee + weightFee;

  return {
    fee: totalFee,
    isFree: false,
  };
}

/**
 * Format phí ship thành string hiển thị
 */
export function formatShippingFee(fee: number, isFree: boolean, reason?: string): string {
  if (isFree) {
    return reason || 'Miễn phí';
  }
  return fee.toLocaleString('vi-VN') + 'đ';
}
