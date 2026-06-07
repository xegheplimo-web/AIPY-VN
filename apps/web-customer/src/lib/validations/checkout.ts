import { z } from "zod";

export const checkoutSchema = z.object({
  // Shipping Information
  fullName: z.string().min(2, "Họ tên phải có ít nhất 2 ký tự").max(100, "Họ tên không được quá 100 ký tự"),
  phone: z.string().regex(/^(0[3-9]\d{8}|84[3-9]\d{8})$/, "Số điện thoại không hợp lệ"),
  email: z.string().email("Email không hợp lệ").optional().or(z.literal("")),
  address: z.string().min(5, "Địa chỉ phải có ít nhất 5 ký tự").max(200, "Địa chỉ không được quá 200 ký tự"),
  city: z.string().min(2, "Thành phố không được để trống"),
  district: z.string().min(2, "Quận/Huyện không được để trống"),
  ward: z.string().min(2, "Phường/Xã không được để trống"),
  
  // Delivery Options
  deliveryMethod: z.enum(["standard", "express", "same-day"], {
    errorMap: () => ({ message: "Vui lòng chọn phương thức giao hàng" }),
  }),
  deliveryTime: z.string().optional(),
  
  // Payment Method
  paymentMethod: z.enum(["cod", "momo", "zalopay", "credit_card"], {
    errorMap: () => ({ message: "Vui lòng chọn phương thức thanh toán" }),
  }),
  
  // Notes
  notes: z.string().max(500, "Ghi chú không được quá 500 ký tự").optional(),
  
  // Terms
  agreeToTerms: z.boolean().refine((val) => val === true, {
    message: "Bạn phải đồng ý với điều khoản và điều kiện",
  }),
});

export type CheckoutFormData = z.infer<typeof checkoutSchema>;
