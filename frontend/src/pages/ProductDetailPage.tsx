import React, { useEffect, useState } from 'react';
import { Product } from '../types';
import { productsApi, recommendationsApi } from '../api/client';
import { useCart } from '../context/CartContext';
import { ProductCard } from '../components/ProductCard';
import {
  ArrowLeft,
  ShoppingBag,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Flame,
  Sparkles,
  RefreshCw,
  Box,
} from 'lucide-react';

interface ProductDetailPageProps {
  productId: string;
  onBack: () => void;
  onSelectProduct: (product: Product) => void;
}

export const ProductDetailPage: React.FC<ProductDetailPageProps> = ({
  productId,
  onBack,
  onSelectProduct,
}) => {
  const [product, setProduct] = useState<Product | null>(null);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const { addToCart } = useCart();

  useEffect(() => {
    const loadDetails = async () => {
      setLoading(true);
      try {
        const data = await productsApi.getById(productId);
        setProduct(data);
        const recs = await recommendationsApi.get(productId, 4);
        setRecommendations(Array.isArray(recs) ? recs : []);
      } catch (err) {
        console.error('Failed to load product details', err);
      } finally {
        setLoading(false);
      }
    };
    loadDetails();
  }, [productId]);

  if (loading) {
    return (
      <div className="py-32 text-center">
        <RefreshCw className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
        <p className="text-sm font-semibold text-slate-500">Loading product telemetry & inventory status...</p>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="py-24 text-center">
        <p className="text-slate-600 font-semibold">Product not found.</p>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold"
        >
          Return to Catalog
        </button>
      </div>
    );
  }

  const availableStock =
    product.inventory?.available_quantity ?? product.available_stock ?? product.stock ?? 0;
  const isOutOfStock = availableStock <= 0;
  const isFlashStock = availableStock === 1;

  const handleAddToCart = async () => {
    if (isOutOfStock) return;
    setIsAdding(true);
    try {
      await addToCart(product.id, quantity);
    } finally {
      setIsAdding(false);
    }
  };

  const title = product.name || product.title || 'Product';
  const priceNum = Number(product.price || 0);
  const comparePrice = product.discount_price
    ? Number(product.discount_price)
    : product.compare_at_price
    ? Number(product.compare_at_price)
    : null;

  const imageSrc =
    product.image_url ||
    (product.images && product.images.length > 0 ? product.images[0] : null) ||
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80';

  return (
    <div className="space-y-12 pb-16">
      {/* Back button */}
      <button
        onClick={onBack}
        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Products
      </button>

      {/* Main Product Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 bg-white rounded-3xl p-8 border border-slate-200 shadow-xs">
        {/* Product Image */}
        <div className="relative rounded-2xl overflow-hidden bg-slate-100 aspect-square">
          <img
            src={imageSrc}
            alt={title}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src =
                'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80';
            }}
          />
          {isFlashStock && (
            <div className="absolute top-4 left-4 bg-rose-600 text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-lg animate-pulse">
              <Flame className="w-4 h-4 fill-white" />
              HOT CONCURRENCY DEMO: 1 UNIT LEFT
            </div>
          )}
        </div>

        {/* Product Details */}
        <div className="flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-700 bg-brand-50 px-2.5 py-1 rounded-md">
                {product.category?.name || product.brand || 'Hardware'}
              </span>
              <span className="text-xs font-mono text-slate-400">SKU: {product.sku}</span>
            </div>

            <h1 className="text-3xl font-extrabold text-slate-900 leading-tight">{title}</h1>

            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-extrabold text-slate-900">
                ${priceNum.toFixed(2)}
              </span>
              {comparePrice && comparePrice > priceNum && (
                <span className="text-base text-slate-400 line-through">
                  ${comparePrice.toFixed(2)}
                </span>
              )}
            </div>

            <p className="text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-4">
              {product.description ||
                'Engineered with premium components for high reliability and modern workflow efficiency.'}
            </p>

            {/* Inventory Status Breakdown */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-slate-600 flex items-center gap-1.5">
                  <Box className="w-4 h-4 text-slate-500" />
                  Inventory Status:
                </span>
                {isOutOfStock ? (
                  <span className="text-rose-600 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Out of stock
                  </span>
                ) : (
                  <span className="text-emerald-700 flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                    {availableStock} units available for reservation
                  </span>
                )}
              </div>
              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200/60 text-center text-xs">
                <div className="p-2 rounded-xl bg-white border border-slate-200">
                  <span className="block text-[10px] text-slate-400 font-medium">Available</span>
                  <span className="font-bold text-emerald-600">{availableStock}</span>
                </div>
                <div className="p-2 rounded-xl bg-white border border-slate-200">
                  <span className="block text-[10px] text-slate-400 font-medium">Reserved</span>
                  <span className="font-bold text-amber-600">
                    {product.inventory?.reserved_quantity ?? 0}
                  </span>
                </div>
                <div className="p-2 rounded-xl bg-white border border-slate-200">
                  <span className="block text-[10px] text-slate-400 font-medium">Sold</span>
                  <span className="font-bold text-slate-800">
                    {product.inventory?.sold_quantity ?? 0}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <div className="flex items-center gap-4">
              {/* Quantity Changer */}
              <div className="flex items-center border border-slate-200 rounded-xl bg-white p-1">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  disabled={quantity <= 1 || isOutOfStock}
                  className="w-8 h-8 flex items-center justify-center font-bold text-slate-600 hover:bg-slate-100 rounded-lg transition disabled:opacity-30"
                >
                  -
                </button>
                <span className="w-10 text-center font-bold text-sm text-slate-800">{quantity}</span>
                <button
                  onClick={() => setQuantity(Math.min(availableStock, quantity + 1))}
                  disabled={quantity >= availableStock || isOutOfStock}
                  className="w-8 h-8 flex items-center justify-center font-bold text-slate-600 hover:bg-slate-100 rounded-lg transition disabled:opacity-30"
                >
                  +
                </button>
              </div>

              {/* Add to Cart button */}
              <button
                onClick={handleAddToCart}
                disabled={isOutOfStock || isAdding}
                className={`flex-1 py-3 px-6 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-md ${
                  isOutOfStock
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-brand-600 hover:bg-brand-700 text-white shadow-brand-500/20 active:scale-98'
                }`}
              >
                {isAdding ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <ShoppingBag className="w-4 h-4" />
                    <span>{isOutOfStock ? 'Sold Out' : 'Add to Shopping Bag'}</span>
                  </>
                )}
              </button>
            </div>

            {/* Concurrency protection explanation */}
            <div className="flex items-center gap-2 text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                Protected by row-level locks (<code className="font-mono text-slate-700">SELECT FOR UPDATE</code>) + atomic conditional decrement upon checkout.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations Carousel */}
      {Array.isArray(recommendations) && recommendations.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <h3 className="text-xl font-bold text-slate-900">Frequently Bought With This Item</h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {recommendations.map((rec) => (
              <ProductCard key={rec.id} product={rec} onSelect={(p) => onSelectProduct(p)} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
