import { useQuery } from "@tanstack/react-query";
import ProductDetail from "@/components/ProductDetail";
import SEO, { BreadcrumbSchema } from "@/components/SEO";

interface Attribute {
  name: string;
  values: string[];
}

interface InventoryItemAPI {
  id: number;
  product_id: string;
  color: string | null;
  attribute1_value: string | null;
  attribute2_value: string | null;
  quantity: number;
  backorder_lead_time_days: number | null;
}

interface InventoryItem {
  color: string | null;
  attribute1_value: string | null;
  attribute2_value: string | null;
  quantity: number;
  backorder_lead_time_days: number | null;
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

  // Load inventory for product
  const { data: inventory } = useQuery<InventoryItem[]>({
    queryKey: ["/api/products", productId, "inventory"],
    queryFn: async () => {
      const response = await fetch(`/api/products/${productId}/inventory`);
      if (!response.ok) return [];
      const data: InventoryItemAPI[] = await response.json();
      return data.map(item => ({
        color: item.color,
        attribute1_value: item.attribute1_value,
        attribute2_value: item.attribute2_value,
        quantity: item.quantity,
        backorder_lead_time_days: item.backorder_lead_time_days
      }));
    },
    enabled: !!productId
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
      <SEO 
        title={product.name}
        description={product.description}
        image={product.images?.[0]}
        type="product"
        product={{
          name: product.name,
          description: product.description,
          price: product.price,
          images: product.images,
          availability: 'InStock'
        }}
      />
      <BreadcrumbSchema 
        items={[
          { name: 'Главная', url: '/' },
          { name: product.name, url: `/product/${product.id}` }
        ]}
      />
      <ProductDetail
        id={product.id}
        name={product.name}
        description={product.description || 'Описание товара'}
        price={product.price}
        images={product.images}
        colors={product.colors}
        attributes={product.attributes}
        inventory={inventory}
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
