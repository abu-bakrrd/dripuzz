import { useState, useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Router, Route, Switch, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { useCart } from "@/hooks/useCart";
import { useFavorites } from "@/hooks/useFavorites";
import Home from "@/pages/Home";
import Cart from "@/pages/Cart";
import Favorites from "@/pages/Favorites";
import Product from "@/pages/Product";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import ThemeApplier from "@/components/ThemeApplier";
import FontLoader from "@/components/FontLoader";
import AdminLogin from "@/pages/admin/AdminLogin";
import AdminLayout from "@/pages/admin/AdminLayout";

interface PendingAction {
  type: 'addToCart' | 'toggleFavorite' | 'navigate';
  productId?: string;
  selectedColor?: string;
  selectedAttributes?: Record<string, string>;
  targetPath?: string;
}

function AppContent() {
  const [location, setLocation] = useLocation();
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  
  const { user, isLoading: isUserLoading } = useAuth();

  const { 
    cartItems, 
    isLoading: isCartLoading, 
    addToCart, 
    updateQuantity, 
    removeFromCart, 
    clearCart 
  } = useCart();
  
  const { 
    favoriteItems, 
    isLoading: isFavoritesLoading, 
    toggleFavorite, 
    favoriteIds 
  } = useFavorites();

  useEffect(() => {
    if (user && pendingAction && !isUserLoading) {
      const action = pendingAction;
      setPendingAction(null);
      
      if (action.type === 'addToCart' && action.productId) {
        addToCart(action.productId, action.selectedColor, action.selectedAttributes);
      } else if (action.type === 'toggleFavorite' && action.productId) {
        toggleFavorite(action.productId);
      }
      
      setLocation(action.targetPath || '/');
    }
  }, [user, isUserLoading]);

  const handleAddToCart = (id: string, selectedColor?: string, selectedAttributes?: Record<string, string>) => {
    if (!user) {
      setPendingAction({ 
        type: 'addToCart', 
        productId: id, 
        selectedColor, 
        selectedAttributes,
        targetPath: location
      });
      setLocation('/registration');
      return;
    }
    addToCart(id, selectedColor, selectedAttributes);
  };

  const handleToggleFavorite = (id: string) => {
    if (!user) {
      setPendingAction({ 
        type: 'toggleFavorite', 
        productId: id,
        targetPath: location
      });
      setLocation('/registration');
      return;
    }
    toggleFavorite(id);
  };

  const handleProductClick = (id: string) => {
    setSelectedProductId(id);
    setLocation(`/product/${id}`);
  };

  const handleQuantityChange = (id: string, quantity: number) => {
    const cartItem = cartItems.find(item => item.cart_id === id || item.id === id);
    updateQuantity({ cartId: cartItem?.cart_id, productId: id, quantity });
  };

  const handleRemoveItem = (id: string) => {
    const cartItem = cartItems.find(item => item.cart_id === id || item.id === id);
    if (cartItem?.cart_id) {
      removeFromCart(cartItem.cart_id);
    }
  };

  const handleClearCart = () => {
    clearCart();
  };

  const transformedCartItems = cartItems.map(item => ({
    id: item.cart_id || item.id,
    name: item.name,
    price: item.price,
    quantity: item.quantity,
    images: item.images,
    selected_color: item.selected_color,
    selected_attributes: item.selected_attributes,
  }));

  const transformedFavoriteItems = favoriteItems.map(item => ({
    id: item.id,
    name: item.name,
    price: item.price,
    images: item.images,
    isFavorite: true,
  }));

  const cartCount = transformedCartItems.reduce((sum, item) => sum + item.quantity, 0);
  const cartItemIds = cartItems.map(item => item.product_id || item.id);

  if (isUserLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    );
  }

  const handleCartClick = () => {
    if (!user) {
      setPendingAction({ 
        type: 'navigate', 
        targetPath: '/cart'
      });
      setLocation('/registration');
      return;
    }
    setLocation('/cart');
  };

  const handleFavoritesClick = () => {
    if (!user) {
      setPendingAction({ 
        type: 'navigate', 
        targetPath: '/favorites'
      });
      setLocation('/registration');
      return;
    }
    setLocation('/favorites');
  };

  const handleAccountClick = () => {
    if (!user) {
      setLocation('/login');
    }
  };

  return (
    <div className="w-full mx-auto bg-background min-h-screen">
      <div className="w-full">
        <Switch>
          <Route path="/admin/login">
            <AdminLogin />
          </Route>
          
          <Route path="/admin">
            <AdminLayout />
          </Route>
          
          <Route path="/login">
            <Login
              onRegisterClick={() => setLocation('/registration')}
              onSuccess={() => {
                if (!pendingAction) {
                  setLocation('/');
                }
              }}
            />
          </Route>
          
          <Route path="/registration">
            <Register
              onLoginClick={() => setLocation('/login')}
              onSuccess={() => {
                if (!pendingAction) {
                  setLocation('/');
                }
              }}
            />
          </Route>
          
          <Route path="/cart">
            {user ? (
              <Cart
                items={transformedCartItems}
                onBack={() => setLocation('/')}
                onQuantityChange={handleQuantityChange}
                onRemoveItem={handleRemoveItem}
                onClearCart={handleClearCart}
              />
            ) : (
              <Register
                onLoginClick={() => setLocation('/login')}
                onSuccess={() => setLocation('/cart')}
              />
            )}
          </Route>
          
          <Route path="/favorites">
            {user ? (
              <Favorites
                items={transformedFavoriteItems}
                onBack={() => setLocation('/')}
                onClearAll={() => {
                  favoriteIds.forEach(id => toggleFavorite(id));
                }}
                onToggleFavorite={handleToggleFavorite}
                onAddToCart={handleAddToCart}
                onProductClick={handleProductClick}
              />
            ) : (
              <Register
                onLoginClick={() => setLocation('/login')}
                onSuccess={() => setLocation('/favorites')}
              />
            )}
          </Route>
          
          <Route path="/product/:id">
            {(params) => {
              const productId = params.id || selectedProductId;
              return (
                <Product
                  productId={productId}
                  onBack={() => setLocation('/')}
                  onAddToCart={handleAddToCart}
                  onToggleFavorite={handleToggleFavorite}
                  isFavorite={favoriteIds.includes(productId)}
                  isInCart={cartItemIds.includes(productId)}
                  onCartClick={() => setLocation('/cart')}
                />
              );
            }}
          </Route>
          
          <Route path="/">
            <Home
              onCartClick={handleCartClick}
              onFavoritesClick={handleFavoritesClick}
              onAccountClick={handleAccountClick}
              onProductClick={handleProductClick}
              cartCount={cartCount}
              favoritesCount={transformedFavoriteItems.length}
              onAddToCart={handleAddToCart}
              onToggleFavorite={handleToggleFavorite}
              favoriteIds={favoriteIds}
              cartItemIds={cartItemIds}
            />
          </Route>
        </Switch>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <Router>
            <ThemeApplier />
            <FontLoader />
            <AppContent />
            <Toaster />
          </Router>
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
