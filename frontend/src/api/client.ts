import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiResponse, AuthTokens, User, Product, Category, Cart, Order, InventoryItem } from '../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request interceptor: Attach JWT token
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('shopflow_access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401 & Token Refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/auth/')) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('shopflow_refresh_token');
      if (!refreshToken) {
        localStorage.removeItem('shopflow_access_token');
        localStorage.removeItem('shopflow_refresh_token');
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        const response = await axios.post<ApiResponse<AuthTokens>>(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newTokens = response.data.data;
        localStorage.setItem('shopflow_access_token', newTokens.access_token);
        localStorage.setItem('shopflow_refresh_token', newTokens.refresh_token);

        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newTokens.access_token}`;
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
        }

        processQueue(null, newTokens.access_token);
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.removeItem('shopflow_access_token');
        localStorage.removeItem('shopflow_refresh_token');
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// API Service modules
export const authApi = {
  login: async (credentials: { email: string; password: string }): Promise<AuthTokens> => {
    const res = await apiClient.post<ApiResponse<AuthTokens>>('/auth/login', credentials);
    return res.data.data;
  },
  register: async (data: { email: string; password: string; full_name: string }): Promise<User> => {
    const res = await apiClient.post<ApiResponse<User>>('/auth/register', data);
    return res.data.data;
  },
  me: async (): Promise<User> => {
    const res = await apiClient.get<ApiResponse<User>>('/auth/me');
    return res.data.data;
  },
  logout: () => {
    localStorage.removeItem('shopflow_access_token');
    localStorage.removeItem('shopflow_refresh_token');
  },
};

export const productsApi = {
  list: async (params?: {
    page?: number;
    limit?: number;
    category?: string;
    search?: string;
    min_price?: number;
    max_price?: number;
    sort?: string;
  }) => {
    const res = await apiClient.get<ApiResponse<any>>('/products', { params });
    const payload = res.data?.data;
    if (payload && Array.isArray(payload.items)) {
      return {
        items: payload.items as Product[],
        total: payload.total || payload.items.length,
        page: payload.page || 1,
        pages: payload.pages || 1,
      };
    }
    if (Array.isArray(payload)) {
      return {
        items: payload as Product[],
        total: payload.length,
        page: 1,
        pages: 1,
      };
    }
    return { items: [] as Product[], total: 0, page: 1, pages: 1 };
  },
  getById: async (id: string): Promise<Product> => {
    const res = await apiClient.get<ApiResponse<Product>>(`/products/${id}`);
    return res.data.data;
  },
  getBySlug: async (slug: string): Promise<Product> => {
    const res = await apiClient.get<ApiResponse<Product>>(`/products/slug/${slug}`);
    return res.data.data;
  },
};

export const categoriesApi = {
  list: async (): Promise<Category[]> => {
    const res = await apiClient.get<ApiResponse<Category[]>>('/categories');
    return Array.isArray(res.data?.data) ? res.data.data : [];
  },
};

export const cartApi = {
  getCart: async (): Promise<Cart> => {
    const res = await apiClient.get<ApiResponse<Cart>>('/cart');
    return res.data.data;
  },
  addItem: async (productId: string, quantity: number = 1): Promise<Cart> => {
    const res = await apiClient.post<ApiResponse<Cart>>('/cart/items', {
      product_id: productId,
      quantity,
    });
    return res.data.data;
  },
  updateItem: async (itemId: string, quantity: number): Promise<Cart> => {
    const res = await apiClient.put<ApiResponse<Cart>>(`/cart/items/${itemId}`, {
      quantity,
    });
    return res.data.data;
  },
  removeItem: async (itemId: string): Promise<Cart> => {
    const res = await apiClient.delete<ApiResponse<Cart>>(`/cart/items/${itemId}`);
    return res.data.data;
  },
  clearCart: async (): Promise<Cart> => {
    const res = await apiClient.delete<ApiResponse<Cart>>('/cart');
    return res.data.data;
  },
};

export const checkoutApi = {
  checkout: async (
    data: {
      shipping_address: any;
      billing_address?: any;
      payment_method?: string;
      simulation_outcome?: string;
    },
    idempotencyKey?: string
  ): Promise<Order> => {
    const key =
      idempotencyKey ||
      (typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : 'idem-' + Math.random().toString(36).substring(2));
    const res = await apiClient.post<ApiResponse<Order>>('/checkout', data, {
      headers: {
        'Idempotency-Key': key,
      },
    });
    return res.data.data;
  },
};

export const ordersApi = {
  list: async (params?: { page?: number; limit?: number; status?: string }) => {
    const res = await apiClient.get<ApiResponse<any>>('/orders', { params });
    const payload = res.data?.data;
    if (payload && Array.isArray(payload.items)) {
      return payload.items as Order[];
    }
    if (Array.isArray(payload)) {
      return payload as Order[];
    }
    return [];
  },
  getById: async (orderId: string): Promise<Order> => {
    const res = await apiClient.get<ApiResponse<Order>>(`/orders/${orderId}`);
    return res.data.data;
  },
  cancel: async (orderId: string): Promise<Order> => {
    const res = await apiClient.post<ApiResponse<Order>>(`/orders/${orderId}/cancel`);
    return res.data.data;
  },
};

export const recommendationsApi = {
  get: async (productId?: string, limit: number = 4): Promise<Product[]> => {
    try {
      const res = await apiClient.get<ApiResponse<any>>('/recommendations', {
        params: { limit },
      });
      const data = res.data?.data;
      if (data && Array.isArray(data.recommendations)) {
        return data.recommendations
          .map((item: any) => item.product)
          .filter(Boolean) as Product[];
      }
      if (Array.isArray(data)) {
        return data as Product[];
      }
      return [];
    } catch {
      return [];
    }
  },
};

export const adminApi = {
  getMetrics: async () => {
    const res = await apiClient.get<ApiResponse<any>>('/admin/dashboard');
    return res.data.data;
  },
  getOrders: async (params?: { page?: number; page_size?: number; status?: string }) => {
    const res = await apiClient.get<ApiResponse<any>>('/admin/orders', { params });
    const payload = res.data?.data;
    if (payload && Array.isArray(payload.items)) {
      return { data: payload.items as Order[] };
    }
    if (Array.isArray(payload)) {
      return { data: payload as Order[] };
    }
    return { data: [] as Order[] };
  },
  updateOrderStatus: async (orderId: string, status: string): Promise<Order> => {
    const res = await apiClient.patch<ApiResponse<Order>>(`/admin/orders/${orderId}/status`, { status });
    return res.data.data;
  },
  getInventory: async () => {
    const res = await apiClient.get<ApiResponse<InventoryItem[]>>('/admin/inventory');
    return Array.isArray(res.data?.data) ? res.data.data : [];
  },
  adjustInventory: async (productId: string, delta: number, reason: string): Promise<InventoryItem> => {
    const res = await apiClient.post<ApiResponse<InventoryItem>>(`/admin/inventory/${productId}/adjust`, {
      delta,
      reason,
    });
    return res.data.data;
  },
  getAuditLogs: async (limit: number = 50) => {
    const res = await apiClient.get<ApiResponse<any[]>>('/admin/audit-logs', { params: { limit } });
    return Array.isArray(res.data?.data) ? res.data.data : [];
  },
  getDlq: async () => {
    const res = await apiClient.get<ApiResponse<any[]>>('/admin/dlq');
    return Array.isArray(res.data?.data) ? res.data.data : [];
  },
};
