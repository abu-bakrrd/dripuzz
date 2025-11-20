import { useQuery } from "@tanstack/react-query";
import ProductDetail from "@/components/ProductDetail";

interface Attribute {
  name: string;
  values: string[];
}

interface ProductData {
  id: string;
  name: string;
  description?: string;
  price: number;
  images: string[];
  category_id: string;
  colors?: string[];
  attributes?: Attribute[];
}

interface ProductProps {
  productId: string;
  onBack: () => void;
  onAddToCart: (id: string, selectedColor?: string, selectedAttributes?: Record<string, string>) => void;
  onToggleFavorite: (id: string) => void;
  isFavorite: boolean;
  isInCart: boolean;
  onCartClick: () => void;
}

export default function Product({
  productId,
  onBack,
  onAddToCart,
  onToggleFavorite,
  isFavorite,
  isInCart,
  onCartClick,
}: ProductProps) {
  // Load product from API
  const { data: product, isLoading, error } = useQuery<ProductData>({
    queryKey: ["/api/products", productId],
    queryFn: async () => {
      const response = await fetch(`/api/products/${productId}`);
      if (!response.ok) throw new Error('Product not found');
      return response.json();
    }
  });
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Загрузка товара...</p>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">Товар не найден</p>
          <button 
            onClick={onBack}
            className="mt-4 text-primary hover:underline"
          >
            Вернуться назад
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-background pb-6">
      <ProductDetail
        id={product.id}
        name={product.name}
        description={product.description || 'Описание товара'}
        price={product.price}
        images={product.images}
        colors={product.colors}
        attributes={product.attributes}
        isFavorite={isFavorite}
        isInCart={isInCart}
        onToggleFavorite={onToggleFavorite}
        onAddToCart={onAddToCart}
        onBack={onBack}
        onCartClick={onCartClick}
      />
    </div>
  );
}
