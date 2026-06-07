export const money = (value: number) => value.toLocaleString('vi-VN') + 'đ';
export const km = (value: number) => value < 1 ? `${Math.round(value * 1000)}m` : `${value.toFixed(1)}km`;
