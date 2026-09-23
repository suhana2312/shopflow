export type Role = 'customer' | 'admin';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface Inventory {
  id?: string;
  product_id?: string;
  available_quantity: number;
  reserved_quantity: number;
  sold_quantity?: number;
  low_stock_threshold?: number;
  is_low_stock?: boolean;
  version?: number;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  title?: string;
  description?: string;
  price: number | string;
  discount_price?: number | string | null;
  compare_at_price?: number | string | null;
  category_id?: string | null;
  category?: Category | null;
  brand?: string | null;
  image_url?: string | null;
  images?: string[];
  is_active: boolean;
  inventory?: Inventory | null;
  stock?: number;
  reserved_stock?: number;
  available_stock?: number;
  created_at?: string;
  updated_at?: string;
}

export interface CartItem {
  id: string;
  cart_id: string;
  product_id: string;
  product: Product;
  quantity: number;
  unit_price: number | string;
  total_price: number | string;
  created_at?: string;
  updated_at?: string;
}

export interface Cart {
  id: string;
  user_id: string;
  items: CartItem[];
  subtotal: number;
  total_items: number;
  created_at?: string;
  updated_at?: string;
}

export type OrderStatus =
  | 'PENDING'
  | 'PAYMENT_PROCESSING'
  | 'CONFIRMED'
  | 'PACKED'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'CANCELLED'
  | 'REFUNDED';

export type PaymentStatus =
  | 'PENDING'
  | 'SUCCESS'
  | 'FAILED'
  | 'REFUNDED';

export interface OrderItem {
  id: string;
  order_id?: string;
  product_id?: string;
  product_name?: string;
  product_title?: string;
  product_sku?: string;
  product_image?: string;
  quantity: number;
  unit_price: number | string;
  subtotal?: number | string;
  total_price?: number | string;
}

export interface Address {
  id?: string;
  full_name: string;
  address_line1?: string;
  street?: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country?: string;
  phone?: string;
}

export interface Payment {
  id: string;
  order_id?: string;
  payment_number?: string;
  transaction_id: string;
  amount: number | string;
  currency?: string;
  status: PaymentStatus | string;
  payment_method?: string;
  failure_reason?: string;
  error_message?: string;
  created_at: string;
}

export interface Order {
  id: string;
  order_number: string;
  user_id: string;
  status: OrderStatus;
  total_amount: number | string;
  subtotal: number | string;
  tax?: number | string;
  tax_amount?: number | string;
  shipping_fee?: number | string;
  shipping_amount?: number | string;
  discount?: number | string;
  discount_amount?: number | string;
  currency?: string;
  shipping_address: Address;
  billing_address?: Address;
  items: OrderItem[];
  payment?: Payment;
  created_at: string;
  updated_at: string;
}

export interface InventoryItem {
  id: string;
  product_id: string;
  product_title?: string;
  product_name?: string;
  product_sku?: string;
  total_quantity?: number;
  reserved_quantity: number;
  available_quantity: number;
  low_stock_threshold: number;
  is_low_stock?: boolean;
  version?: number;
  updated_at?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  } | null;
  request_id?: string | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
