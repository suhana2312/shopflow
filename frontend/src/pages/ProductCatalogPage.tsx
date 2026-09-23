import React, { useEffect, useState } from 'react';
import { Product, Category } from '../types';
import { productsApi, categoriesApi, recommendationsApi } from '../api/client';
import { ProductCard } from '../components/ProductCard';
import { Search, SlidersHorizontal, Sparkles, Zap, Flame, RefreshCw } from 'lucide-react';

interface ProductCatalogPageProps {
  onSelectProduct: (product: Product) => void;
}

export const ProductCatalogPage: React.FC<ProductCatalogPageProps> = ({ onSelectProduct }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('created_at_desc');

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const res = await productsApi.list({
        category: selectedCategory ?? undefined,
        search: searchQuery.trim() || undefined,
        sort: sortBy,
        limit: 50,
      });
      const items = Array.isArray(res.items) ? res.items : [];
      setProducts(items);
    } catch (err) {
      console.error('Failed to load products', err);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const cats = await categoriesApi.list();
        setCategories(Array.isArray(cats) ? cats : []);
      } catch (err) {
        console.error('Failed to load categories', err);
        setCategories([]);
      }
    };
    loadCategories();
  }, []);

  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        const recs = await recommendationsApi.get(undefined, 4);
        setRecommendations(Array.isArray(recs) ? recs : []);
      } catch (err) {
        console.error('Failed to load recommendations', err);
        setRecommendations([]);
      }
    };
    loadRecommendations();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProducts();
    }, 250);
    return () => clearTimeout(timer);
  }, [selectedCategory, searchQuery, sortBy]);

  // Flash item highlight
  const safeProducts = Array.isArray(products) ? products : [];
  const flashItem = safeProducts.find((p) => {
    const avail = p.inventory?.available_quantity ?? p.available_stock ?? p.stock;
    return avail === 1;
  });

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Banner with Concurrency Callout */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-950 text-white p-8 sm:p-12 shadow-xl border border-slate-800">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-2xl relative z-10 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30 text-xs font-semibold">
            <Zap className="w-3.5 h-3.5 fill-brand-400" />
            <span>High-Throughput Concurrency Engine</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Real-Time Inventory & Order Architecture
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Every inventory check is backed by atomic conditional decrement and row-level locking. Orders stream status transitions over WebSockets with zero overselling.
          </p>

          {/* Flash race demo callout */}
          {flashItem && (
            <div
              onClick={() => onSelectProduct(flashItem)}
              className="mt-6 p-4 rounded-2xl bg-slate-800/80 border border-rose-500/40 hover:border-rose-400 transition cursor-pointer flex items-center justify-between gap-4 backdrop-blur-sm shadow-md"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-rose-600/30 flex items-center justify-center text-rose-400 shrink-0">
                  <Flame className="w-5 h-5 fill-rose-500" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs uppercase font-extrabold tracking-wider text-rose-400">
                      Concurrency Race Demo
                    </span>
                    <span className="text-[10px] bg-rose-900/60 text-rose-200 px-2 py-0.5 rounded font-mono">
                      Stock: 1
                    </span>
                  </div>
                  <p className="text-sm font-bold text-white mt-0.5">{flashItem.name || flashItem.title}</p>
                </div>
              </div>
              <span className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white shrink-0">
                Test Race →
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Filter and Search Controls */}
      <section className="space-y-4">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          {/* Search Input */}
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search products by title, SKU, or specs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition shadow-xs"
            />
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Sort:</span>
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="text-xs font-medium bg-white border border-slate-200 rounded-xl px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-xs"
            >
              <option value="created_at_desc">Newest Arrivals</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="name_asc">Name: A to Z</option>
            </select>
          </div>
        </div>

        {/* Category Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition shadow-xs ${
              selectedCategory === null
                ? 'bg-slate-900 text-white shadow-slate-900/10'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            All Products
          </button>
          {Array.isArray(categories) &&
            categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.slug || cat.id)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition shadow-xs ${
                  selectedCategory === (cat.slug || cat.id)
                    ? 'bg-slate-900 text-white shadow-slate-900/10'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                }`}
              >
                {cat.name}
              </button>
            ))}
        </div>
      </section>

      {/* Product Grid */}
      <section>
        {loading ? (
          <div className="py-24 text-center">
            <RefreshCw className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
            <p className="text-sm font-semibold text-slate-500">Querying inventory with Redis cache...</p>
          </div>
        ) : safeProducts.length === 0 ? (
          <div className="py-20 text-center bg-white rounded-2xl border border-dashed border-slate-300 p-8">
            <p className="text-slate-600 font-semibold">No products found matching your search criteria.</p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory(null);
              }}
              className="mt-4 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {safeProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onSelect={(p) => onSelectProduct(p)}
              />
            ))}
          </div>
        )}
      </section>

      {/* AI Recommendations Section */}
      {Array.isArray(recommendations) && recommendations.length > 0 && (
        <section className="bg-gradient-to-r from-purple-50/60 via-brand-50/40 to-blue-50/60 rounded-3xl p-8 border border-purple-100">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-600 text-white flex items-center justify-center shadow-sm">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">AI-Powered Recommendations</h3>
                <p className="text-xs text-slate-500">
                  Scored across collaborative catalog signals, category affinity & trending velocity
                </p>
              </div>
            </div>
            <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full bg-purple-100 text-purple-800">
              Engine: Active
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {recommendations.map((rec) => (
              <ProductCard
                key={`rec-${rec.id}`}
                product={rec}
                onSelect={(p) => onSelectProduct(p)}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
