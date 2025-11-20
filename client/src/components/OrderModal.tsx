import { Button } from "@/components/ui/button";
import { useConfig } from "@/hooks/useConfig";

interface OrderItem {
  name: string;
  quantity: number;
  price: number;
}

interface OrderModalProps {
  isOpen: boolean;
  items: OrderItem[];
  total: number;
  onClose: () => void;
  onOrderComplete: () => void;
}

export default function OrderModal({
  isOpen,
  items,
  total,
  onClose,
  onOrderComplete,
}: OrderModalProps) {
  const { config, formatPrice } = useConfig();
  
  if (!isOpen) return null;

  const handleConfirm = () => {
    onOrderComplete();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="modal-order">
      <div className="bg-background rounded-lg max-w-md w-full p-6 shadow-lg">
        <h2 className="text-lg font-semibold mb-4" data-testid="text-modal-title">
          Вы заказали:
        </h2>
        
        <div className="space-y-2 mb-4">
          {items.map((item, index) => (
            <div key={index} className="text-sm" data-testid={`text-order-item-${index}`}>
              • {item.name} — {item.quantity} шт. — {formatPrice(item.price)}
            </div>
          ))}
        </div>

        <div className="border-t border-border pt-3 mb-4">
          <div className="font-semibold" data-testid="text-order-total">
            Итого: {formatPrice(total)}
          </div>
        </div>

        <p className="text-sm text-muted-foreground mb-6">
          Наш менеджер <span className="text-primary">{config?.managerContact}</span> свяжется с вами для оформления.
        </p>

        <Button
          onClick={handleConfirm}
          className="w-full"
          data-testid="button-modal-close"
        >
          ОК
        </Button>
      </div>
    </div>
  );
}
