import { Minus, Plus, Trash2, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useConfig } from "@/hooks/useConfig";

interface CartItemProps {
  id: string;
  name: string;
  price: number;
  quantity: number;
  images: string[];
  onQuantityChange: (id: string, quantity: number) => void;
  onRemove: (id: string) => void;
}

export default function CartItem({
  id,
  name,
  price,
  quantity,
  images,
  onQuantityChange,
  onRemove,
}: CartItemProps) {
  const { formatPrice } = useConfig();
  const [imageError, setImageError] = useState(false);

  return (
    <div className="flex gap-3 p-3 bg-card rounded-md border border-card-border" data-testid={`cart-item-${id}`}>
      <div className="w-20 h-20 rounded-md bg-muted flex items-center justify-center overflow-hidden">
        {imageError ? (
          <ImageIcon className="w-10 h-10 text-muted-foreground/40" />
        ) : (
          <img
            src={images[0]}
            alt={name}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium mb-1 line-clamp-2" data-testid={`text-cart-item-name-${id}`}>
          {name}
        </h3>
        <p className="text-sm font-semibold mb-2" data-testid={`text-cart-item-price-${id}`}>
          {formatPrice(price)}
        </p>
        
        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="outline"
            onClick={() => onQuantityChange(id, quantity - 1)}
            disabled={quantity <= 1}
            className="h-7 w-7"
            data-testid={`button-decrease-${id}`}
          >
            <Minus className="w-3 h-3" />
          </Button>
          
          <span className="text-sm font-medium min-w-6 text-center" data-testid={`text-quantity-${id}`}>
            {quantity}
          </span>
          
          <Button
            size="icon"
            variant="outline"
            onClick={() => onQuantityChange(id, quantity + 1)}
            className="h-7 w-7"
            data-testid={`button-increase-${id}`}
          >
            <Plus className="w-3 h-3" />
          </Button>
        </div>
      </div>

      <Button
        size="icon"
        variant="ghost"
        onClick={() => onRemove(id)}
        className="h-8 w-8 text-destructive"
        data-testid={`button-remove-${id}`}
      >
        <Trash2 className="w-4 h-4" />
      </Button>
    </div>
  );
}
