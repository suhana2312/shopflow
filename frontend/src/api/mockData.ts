import { Product, Category, Order, InventoryItem, User, AuthTokens } from '../types';

export const MOCK_CATEGORIES: Category[] = [
  { id: 'cat-1', name: 'Laptops & Computers', slug: 'laptops-computers', description: 'High-performance laptops, ultrabooks, and workstations' },
  { id: 'cat-2', name: 'Audio & Sound', slug: 'audio-sound', description: 'Premium noise-cancelling headphones, earbuds, and speakers' },
  { id: 'cat-3', name: 'Keyboards & Mice', slug: 'keyboards-mice', description: 'Mechanical keyboards, ergonomic mice, and desk pads' },
  { id: 'cat-4', name: 'Displays & Monitors', slug: 'displays-monitors', description: 'Color-accurate 4K/UHD and high-refresh-rate displays' },
  { id: 'cat-5', name: 'Accessories & Docks', slug: 'accessories-docks', description: 'Thunderbolt docks, ergonomic stands, and streaming gear' },
];

export const MOCK_PRODUCTS: Product[] = [
  {
    id: 'prod-flash-01',
    sku: 'FLASH-PROMO-01',
    name: 'Limited Edition Mechanical Switch Tester (Stock = 1)',
    title: 'Limited Edition Mechanical Switch Tester (Stock = 1)',
    description: 'Exclusive collectible 9-key switch tester with novelty keycaps. Flash sale item with exactly 1 unit in stock for concurrency testing!',
    price: 29.99,
    category_id: 'cat-3',
    brand: 'KeyCraft',
    image_url: 'https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-flash-01',
      product_id: 'prod-flash-01',
      total_quantity: 1,
      reserved_quantity: 0,
      available_quantity: 1,
      low_stock_threshold: 2,
    },
  },
  {
    id: 'prod-lap-01',
    sku: 'LAP-PRO-15',
    name: 'UltraBook Pro 15.6"',
    title: 'UltraBook Pro 15.6"',
    description: '3.2GHz 16-Core processor, 32GB RAM, 1TB NVMe SSD, OLED 120Hz display with aluminum chassis.',
    price: 1299.99,
    discount_price: 1199.99,
    category_id: 'cat-1',
    brand: 'AeroTech',
    image_url: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-lap-01',
      product_id: 'prod-lap-01',
      total_quantity: 25,
      reserved_quantity: 0,
      available_quantity: 25,
      low_stock_threshold: 5,
    },
  },
  {
    id: 'prod-desk-01',
    sku: 'DESK-APEX-X',
    name: 'Gaming Rig Apex X',
    title: 'Gaming Rig Apex X',
    description: 'Liquid-cooled gaming desktop with RTX 4080, 64GB DDR5, PCIe 5.0 storage, tempered glass case.',
    price: 1899.99,
    category_id: 'cat-1',
    brand: 'ApexForce',
    image_url: 'https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-desk-01',
      product_id: 'prod-desk-01',
      total_quantity: 10,
      reserved_quantity: 0,
      available_quantity: 10,
      low_stock_threshold: 3,
    },
  },
  {
    id: 'prod-kb-01',
    sku: 'KB-MECH-01',
    name: 'Custom Mechanical Keyboard 75%',
    title: 'Custom Mechanical Keyboard 75%',
    description: 'Hot-swappable linear switches, PBT double-shot keycaps, RGB backlighting, gasket mounted.',
    price: 129.99,
    discount_price: 109.99,
    category_id: 'cat-3',
    brand: 'KeyCraft',
    image_url: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-kb-01',
      product_id: 'prod-kb-01',
      total_quantity: 50,
      reserved_quantity: 0,
      available_quantity: 50,
      low_stock_threshold: 10,
    },
  },
  {
    id: 'prod-mse-01',
    sku: 'MSE-ERGO-02',
    name: 'Ergonomic Precision Wireless Mouse',
    title: 'Ergonomic Precision Wireless Mouse',
    description: 'Dual Bluetooth and 2.4GHz connectivity, 8K DPI sensor, infinite hyper-scroll wheel, 70-day battery.',
    price: 69.99,
    category_id: 'cat-3',
    brand: 'KeyCraft',
    image_url: 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-mse-01',
      product_id: 'prod-mse-01',
      total_quantity: 40,
      reserved_quantity: 0,
      available_quantity: 40,
      low_stock_threshold: 8,
    },
  },
  {
    id: 'prod-mon-01',
    sku: 'MON-4K-27',
    name: 'StudioVision 27" 4K HDR Monitor',
    title: 'StudioVision 27" 4K HDR Monitor',
    description: '99% DCI-P3 color gamut, 400 nits brightness, USB-C 90W Power Delivery, height-adjustable stand.',
    price: 499.99,
    discount_price: 459.99,
    category_id: 'cat-4',
    brand: 'ViewMaster',
    image_url: 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-mon-01',
      product_id: 'prod-mon-01',
      total_quantity: 15,
      reserved_quantity: 0,
      available_quantity: 15,
      low_stock_threshold: 5,
    },
  },
  {
    id: 'prod-aud-01',
    sku: 'AUD-ANC-PRO',
    name: 'SonicAir Pro Wireless ANC Headphones',
    title: 'SonicAir Pro Wireless ANC Headphones',
    description: 'Hybrid Active Noise Cancellation, 40mm beryllium drivers, Spatial Audio, 45-hour battery life.',
    price: 199.99,
    discount_price: 179.99,
    category_id: 'cat-2',
    brand: 'SonicAir',
    image_url: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-aud-01',
      product_id: 'prod-aud-01',
      total_quantity: 30,
      reserved_quantity: 0,
      available_quantity: 30,
      low_stock_threshold: 10,
    },
  },
  {
    id: 'prod-acc-01',
    sku: 'ACC-STAND-01',
    name: 'Precision Aluminum Laptop Stand',
    title: 'Precision Aluminum Laptop Stand',
    description: 'CNC machined aerospace aluminum, ergonomic viewing angle, heat dissipation ventilation cutout.',
    price: 49.99,
    category_id: 'cat-5',
    brand: 'DeskPro',
    image_url: 'https://images.unsplash.com/photo-1616353071855-2c045c4458ae?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1616353071855-2c045c4458ae?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-acc-01',
      product_id: 'prod-acc-01',
      total_quantity: 60,
      reserved_quantity: 0,
      available_quantity: 60,
      low_stock_threshold: 15,
    },
  },
  {
    id: 'prod-acc-02',
    sku: 'ACC-DOCK-10',
    name: '10-in-1 Thunderbolt 4 Docking Station',
    title: '10-in-1 Thunderbolt 4 Docking Station',
    description: 'Dual 4K@60Hz display support, 100W PD charging, 2.5G Gigabit Ethernet, SD card reader, 4x USB 3.2.',
    price: 179.99,
    discount_price: 159.99,
    category_id: 'cat-5',
    brand: 'DeskPro',
    image_url: 'https://images.unsplash.com/photo-1544652478-6653e09f18a2?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1544652478-6653e09f18a2?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-acc-02',
      product_id: 'prod-acc-02',
      total_quantity: 20,
      reserved_quantity: 0,
      available_quantity: 20,
      low_stock_threshold: 5,
    },
  },
  {
    id: 'prod-cam-01',
    sku: 'CAM-4K-PRO',
    name: 'StreamClear 4K Pro Webcam',
    title: 'StreamClear 4K Pro Webcam',
    description: 'Sony STARVIS CMOS sensor, dual omnidirectional noise-cancelling mics, HDR auto light correction.',
    price: 139.99,
    category_id: 'cat-5',
    brand: 'StreamClear',
    image_url: 'https://images.unsplash.com/photo-1588508065123-287b28e013da?auto=format&fit=crop&w=800&q=80',
    images: ['https://images.unsplash.com/photo-1588508065123-287b28e013da?auto=format&fit=crop&w=800&q=80'],
    is_active: true,
    inventory: {
      id: 'inv-cam-01',
      product_id: 'prod-cam-01',
      total_quantity: 25,
      reserved_quantity: 0,
      available_quantity: 25,
      low_stock_threshold: 5,
    },
  },
];

// Persistent local simulated store for GitHub Pages demo mode
export const getStoredInventory = (): Product[] => {
  try {
    const saved = localStorage.getItem('shopflow_demo_products');
    if (saved) return JSON.parse(saved);
  } catch {}
  return MOCK_PRODUCTS;
};

export const saveStoredInventory = (products: Product[]) => {
  try {
    localStorage.setItem('shopflow_demo_products', JSON.stringify(products));
  } catch {}
};

export const getStoredOrders = (): Order[] => {
  try {
    const saved = localStorage.getItem('shopflow_demo_orders');
    if (saved) return JSON.parse(saved);
  } catch {}
  return [
    {
      id: 'ord-demo-01',
      order_number: 'ORD-98421',
      user_id: 'user-cust-01',
      status: 'CONFIRMED',
      total_amount: 147.98,
      subtotal: 119.99,
      shipping_fee: 15.0,
      tax: 12.99,
      shipping_address: {
        full_name: 'Alex Johnson',
        street: '100 Silicon Ave',
        city: 'San Francisco',
        state: 'CA',
        postal_code: '94107',
        country: 'United States',
      },
      items: [
        {
          id: 'item-demo-01',
          product_id: 'prod-kb-01',
          product_name: 'Custom Mechanical Keyboard 75%',
          quantity: 1,
          unit_price: 109.99,
          subtotal: 109.99,
        },
      ],
      created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
      updated_at: new Date(Date.now() - 3600000).toISOString(),
    },
  ];
};

export const saveStoredOrders = (orders: Order[]) => {
  try {
    localStorage.setItem('shopflow_demo_orders', JSON.stringify(orders));
  } catch {}
};
