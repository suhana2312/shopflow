import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { Cart } from '../types';
import { cartApi } from '../api/client';
import { useAuth } from './AuthContext';
import { useToast } from './ToastContext';

interface CartContextType {
  cart: Cart | null;
  itemsCount: number;
  subtotal: number;
  loading: boolean;
  addToCart: (productId: string, quantity?: number) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { isAuthenticated } = useAuth();
  const { success, error } = useToast();

  const refreshCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null);
      return;
    }
    try {
      setLoading(true);
      const data = await cartApi.getCart();
      setCart(data);
    } catch (err: any) {
      console.error('Failed to load cart:', err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const addToCart = async (productId: string, quantity: number = 1) => {
    if (!isAuthenticated) {
      error('Sign In Required', 'Please sign in to add products to your cart.');
      return;
    }
    try {
      setLoading(true);
      const updated = await cartApi.addItem(productId, quantity);
      setCart(updated);
      success('Added to Cart', 'Item has been added to your shopping bag.');
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not add item to cart.';
      error('Add to Cart Failed', msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, quantity: number) => {
    try {
      setLoading(true);
      if (quantity <= 0) {
        await removeItem(itemId);
      } else {
        const updated = await cartApi.updateItem(itemId, quantity);
        setCart(updated);
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not update item quantity.';
      error('Update Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  const removeItem = async (itemId: string) => {
    try {
      setLoading(true);
      const updated = await cartApi.removeItem(itemId);
      setCart(updated);
      success('Item Removed', 'Item was removed from your cart.');
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not remove item.';
      error('Remove Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  const clearCart = async () => {
    try {
      setLoading(true);
      const updated = await cartApi.clearCart();
      setCart(updated);
    } catch (err: any) {
      console.error('Failed to clear cart:', err);
    } finally {
      setLoading(false);
    }
  };

  const itemsCount = cart?.items ? cart.items.reduce((sum, item) => sum + item.quantity, 0) : 0;
  const subtotal = cart?.subtotal || 0;

  return (
    <CartContext.Provider
      value={{
        cart,
        itemsCount,
        subtotal,
        loading,
        addToCart,
        updateQuantity,
        removeItem,
        clearCart,
        refreshCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
