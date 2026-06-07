/**
 * Global Error Handler for Frontend
 * Handles unhandled promise rejections and global errors
 */

import { toast } from 'sonner';

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled Promise Rejection:', event.reason);

  // Show user-friendly error message
  toast.error('Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.', {
    description: event.reason?.message || 'Lỗi hệ thống',
    duration: 5000,
  });

  // Prevent default browser error logging
  event.preventDefault();
});

// Handle global errors
window.addEventListener('error', (event) => {
  console.error('Global Error:', event.error);

  // Show user-friendly error message
  toast.error('Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.', {
    description: event.message || 'Lỗi hệ thống',
    duration: 5000,
  });
});

// Helper function for API error handling
export function handleApiError(error: any): string {
  if (error?.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        return data?.detail || 'Yêu cầu không hợp lệ';
      case 401:
        return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
      case 403:
        return 'Bạn không có quyền thực hiện hành động này.';
      case 404:
        return 'Không tìm thấy tài nguyên.';
      case 429:
        return 'Quá nhiều yêu cầu. Vui lòng thử lại sau.';
      case 500:
        return 'Lỗi máy chủ. Vui lòng thử lại sau.';
      default:
        return data?.detail || 'Lỗi không xác định';
    }
  } else if (error?.request) {
    // Request made but no response
    return 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng.';
  } else {
    // Error in setting up request
    return error?.message || 'Lỗi không xác định';
  }
}

// Wrapper for async operations with error handling
export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  errorMessage: string = 'Đã xảy ra lỗi'
): Promise<T | null> {
  try {
    return await operation();
  } catch (error) {
    const message = handleApiError(error);
    toast.error(errorMessage, {
      description: message,
      duration: 5000,
    });
    return null;
  }
}
