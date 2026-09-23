import React, { useState } from 'react';
import { Product } from '../types';
import { ShoppingBag, Flame, AlertCircle, CheckCircle } from 'lucide-react';
import { useCart } from '../context/CartContext';

interface ProductCardProps {
  product: Product;
  onSelect?: (product: Product) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onSelect }) => {
  const { addToCart } = useCart();
  const [isAdding, setIsAdding] = useState(false);

  const availableStock =
    product.inventory?.available_quantity ?? product.available_stock ?? product.stock ?? 0;
  const isOutOfStock = availableStock <= 0;
  const isFlashStock = availableStock === 1;
  const isLowStock = availableStock > 1 && availableStock <= 3;

  const handleAdd = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isOutOfStock) return;
    setIsAdding(true);
    try {
      await addToCart(product.id, 1);
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
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80';

  return (
    <div
      onClick={() => onSelect?.(product)}
      className="group relative bg-white rounded-2xl border border-slate-200 shadow-xs hover:shadow-xl hover:border-brand-200 transition-all duration-300 flex flex-col overflow-hidden cursor-pointer"
    >
      {/* Stock & Discount Badges */}
      <div className="absolute top-3 left-3 z-10 flex flex-col gap-1.5 items-start">
        {isFlashStock && (
          <span className="flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full bg-rose-600 text-white shadow-md animate-pulse">
            <Flame className="w-3.5 h-3.5 fill-white" />
            ONLY 1 LEFT! (Flash Race)
          </span>
        )}
        {isLowStock && (
          <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500 text-white shadow-xs">
            <AlertCircle className="w-3 h-3" />
            Only {availableStock} left
          </span>
        )}
        {isOutOfStock && (
          <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-slate-800 text-slate-200 shadow-xs">
            Sold Out
          </span>
        )}
      </div>

      {/* Image container */}
      <div className="relative w-full aspect-4/3 bg-slate-100 overflow-hidden">
        <img
          src={imageSrc}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80';
          }}
        />
        {comparePrice && comparePrice > priceNum && (
          <div className="absolute top-3 right-3 bg-brand-600 text-white text-[11px] font-bold px-2 py-0.5 rounded-full shadow-sm">
            Save ${(comparePrice - priceNum).toFixed(2)}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          {/* Category & SKU */}
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5 font-medium">
            <span>{product.category?.name || product.brand || 'Accessories'}</span>
            <span className="font-mono text-[10px] text-slate-400">SKU: {product.sku}</span>
          </div>

          <h3 className="font-bold text-slate-900 group-hover:text-brand-700 transition-colors line-clamp-1 text-base">
            {title}
          </h3>

          <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
            {product.description || 'High performance merchandise engineered for everyday excellence.'}
          </p>
        </div>

        {/* Pricing & Add To Cart Button */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-extrabold text-slate-900">
                ${priceNum.toFixed(2)}
              </span>
              {comparePrice && comparePrice > priceNum && (
                <span className="text-xs text-slate-400 line-through">
                  ${comparePrice.toFixed(2)}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1 text-[11px] mt-0.5">
              {!isOutOfStock ? (
                <span className="text-emerald-700 font-medium flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-emerald-500" />
                  {availableStock} available
                </span>
              ) : (
                <span className="text-rose-600 font-medium">Out of stock</span>
              )}
            </div>
          </div>

          <button
            onClick={handleAdd}
            disabled={isOutOfStock || isAdding}
            className={`p-2.5 rounded-xl font-semibold transition-all flex items-center justify-center shadow-xs ${
              isOutOfStock
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-slate-900 hover:bg-brand-600 text-white active:scale-95 shadow-slate-900/10'
            }`}
            title={isOutOfStock ? 'Item is sold out' : 'Add to cart'}
          >
            {isAdding ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <ShoppingBag className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
