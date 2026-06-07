import { z } from "zod";

export const userRegistrationSchema = z.object({
  // Basic Information
  fullName: z.string().min(2, "Họ tên phải có ít nhất 2 ký tự").max(100, "Họ tên không được quá 100 ký tự"),
  email: z.string().email("Email không hợp lệ"),
  phone: z.string().regex(/^(0[3-9]\d{8}|84[3-9]\d{8})$/, "Số điện thoại không hợp lệ"),
  
  // Password
  password: z.string()
    .min(8, "Mật khẩu phải có ít nhất 8 ký tự")
    .regex(/[A-Z]/, "Mật khẩu phải có ít nhất 1 chữ hoa")
    .regex(/[a-z]/, "Mật khẩu phải có ít nhất 1 chữ thường")
    .regex(/[0-9]/, "Mật khẩu phải có ít nhất 1 số"),
  confirmPassword: z.string(),
  
  // Address (Optional)
  address: z.string().max(200, "Địa chỉ không được quá 200 ký tự").optional(),
  city: z.string().optional(),
  district: z.string().optional(),
  
  // Terms
  agreeToTerms: z.boolean().refine((val) => val === true, {
    message: "Bạn phải đồng ý với điều khoản và điều kiện",
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Mật khẩu xác nhận không khớp",
  path: ["confirmPassword"],
});

export type UserRegistrationFormData = z.infer<typeof userRegistrationSchema>;

export const userProfileSchema = z.object({
  // Basic Information
  fullName: z.string().min(2, "Họ tên phải có ít nhất 2 ký tự").max(100, "Họ tên không được quá 100 ký tự"),
  email: z.string().email("Email không hợp lệ"),
  phone: z.string().regex(/^(0[3-9]\d{8}|84[3-9]\d{8})$/, "Số điện thoại không hợp lệ"),
  
  // Address
  address: z.string().max(200, "Địa chỉ không được quá 200 ký tự").optional(),
  city: z.string().optional(),
  district: z.string().optional(),
  ward: z.string().optional(),
  
  // Preferences
  language: z.enum(["vi", "en"]).optional(),
  currency: z.enum(["VND", "USD"]).optional(),
  
  // Notification Preferences
  emailNotifications: z.boolean().optional(),
  smsNotifications: z.boolean().optional(),
  pushNotifications: z.boolean().optional(),
});

export type UserProfileFormData = z.infer<typeof userProfileSchema>;

export const userLoginSchema = z.object({
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(1, "Mật khẩu không được để trống"),
  rememberMe: z.boolean().optional(),
});

export type UserLoginFormData = z.infer<typeof userLoginSchema>;
