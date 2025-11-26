import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useConfig } from "@/hooks/useConfig";
import { X, MapPin, CreditCard, Loader2 } from "lucide-react";

interface OrderItem {
  id: string;
  name: string;
  quantity: number;
  price: number;
  selected_color?: string;
  selected_attributes?: Record<string, string>;
}

interface DeliveryInfo {
  address: string;
  lat: number | null;
  lng: number | null;
  customerName: string;
  customerPhone: string;
}

interface CheckoutModalProps {
  isOpen: boolean;
  items: OrderItem[];
  total: number;
  onClose: () => void;
  onPaymentSelect: (paymentMethod: string, deliveryInfo: DeliveryInfo) => Promise<string | null>;
}

declare global {
  interface Window {
    ymaps: any;
  }
}

export default function CheckoutModal({
  isOpen,
  items,
  total,
  onClose,
  onPaymentSelect,
}: CheckoutModalProps) {
  const { config, formatPrice } = useConfig();
  const [step, setStep] = useState<'delivery' | 'payment'>('delivery');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<string | null>(null);
  
  const [deliveryInfo, setDeliveryInfo] = useState<DeliveryInfo>({
    address: '',
    lat: null,
    lng: null,
    customerName: '',
    customerPhone: '',
  });

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const placemarkerRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setStep('delivery');
      setSelectedPayment(null);
      setDeliveryInfo({
        address: '',
        lat: null,
        lng: null,
        customerName: '',
        customerPhone: '',
      });
      return;
    }

    const yandexApiKey = config?.yandexMaps?.apiKey;
    if (!yandexApiKey) {
      setMapError('API ключ Yandex Maps не настроен');
      return;
    }

    if (window.ymaps) {
      initMap();
      return;
    }

    const script = document.createElement('script');
    script.src = `https://api-maps.yandex.ru/2.1/?apikey=${yandexApiKey}&lang=ru_RU`;
    script.async = true;
    script.onload = () => {
      window.ymaps.ready(() => {
        setMapLoaded(true);
        initMap();
      });
    };
    script.onerror = () => {
      setMapError('Ошибка загрузки Yandex Maps');
    };
    document.head.appendChild(script);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.destroy();
        mapInstanceRef.current = null;
      }
    };
  }, [isOpen, config?.yandexMaps?.apiKey]);

  const initMap = () => {
    if (!mapContainerRef.current || !window.ymaps) return;

    const defaultCenter = config?.yandexMaps?.defaultCenter || [41.311081, 69.240562];
    const defaultZoom = config?.yandexMaps?.defaultZoom || 12;

    try {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.destroy();
      }

      mapInstanceRef.current = new window.ymaps.Map(mapContainerRef.current, {
        center: defaultCenter,
        zoom: defaultZoom,
        controls: ['zoomControl', 'geolocationControl'],
      });

      placemarkerRef.current = new window.ymaps.Placemark(
        defaultCenter,
        { hintContent: 'Переместите маркер на адрес доставки' },
        { draggable: true, preset: 'islands#redDotIcon' }
      );

      mapInstanceRef.current.geoObjects.add(placemarkerRef.current);

      placemarkerRef.current.events.add('dragend', async function () {
        const coords = placemarkerRef.current.geometry.getCoordinates();
        await geocodeCoords(coords);
      });

      mapInstanceRef.current.events.add('click', async function (e: any) {
        const coords = e.get('coords');
        placemarkerRef.current.geometry.setCoordinates(coords);
        await geocodeCoords(coords);
      });

      setMapLoaded(true);
    } catch (error) {
      console.error('Map initialization error:', error);
      setMapError('Ошибка инициализации карты');
    }
  };

  const geocodeCoords = async (coords: [number, number]) => {
    try {
      const result = await window.ymaps.geocode(coords);
      const firstGeoObject = result.geoObjects.get(0);
      const address = firstGeoObject.getAddressLine();
      
      setDeliveryInfo(prev => ({
        ...prev,
        address,
        lat: coords[0],
        lng: coords[1],
      }));
    } catch (error) {
      console.error('Geocoding error:', error);
    }
  };

  const handleAddressSearch = async () => {
    if (!deliveryInfo.address || !window.ymaps) return;

    try {
      const result = await window.ymaps.geocode(deliveryInfo.address);
      const firstGeoObject = result.geoObjects.get(0);
      
      if (firstGeoObject) {
        const coords = firstGeoObject.geometry.getCoordinates();
        const address = firstGeoObject.getAddressLine();
        
        placemarkerRef.current?.geometry.setCoordinates(coords);
        mapInstanceRef.current?.setCenter(coords, 16);
        
        setDeliveryInfo(prev => ({
          ...prev,
          address,
          lat: coords[0],
          lng: coords[1],
        }));
      }
    } catch (error) {
      console.error('Address search error:', error);
    }
  };

  const handleContinueToPayment = () => {
    if (!deliveryInfo.address || !deliveryInfo.customerName || !deliveryInfo.customerPhone) {
      return;
    }
    setStep('payment');
  };

  const handlePayment = async (method: string) => {
    setIsLoading(true);
    setSelectedPayment(method);
    
    try {
      const paymentUrl = await onPaymentSelect(method, deliveryInfo);
      
      if (paymentUrl) {
        window.location.href = paymentUrl;
      }
    } catch (error) {
      console.error('Payment error:', error);
      setIsLoading(false);
      setSelectedPayment(null);
    }
  };

  if (!isOpen) return null;

  const isDeliveryValid = deliveryInfo.address && deliveryInfo.customerName && deliveryInfo.customerPhone;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-background rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="sticky top-0 bg-background border-b border-border p-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {step === 'delivery' ? 'Адрес доставки' : 'Способ оплаты'}
          </h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="p-4">
          {step === 'delivery' ? (
            <div className="space-y-4">
              <div className="bg-muted rounded-lg p-3 mb-4">
                <div className="text-sm text-muted-foreground mb-1">Сумма заказа:</div>
                <div className="text-xl font-bold text-primary">{formatPrice(total)}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {config?.delivery?.freeDeliveryNote || 'Доставка оплачивается при получении'}
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <Label htmlFor="customerName">Ваше имя *</Label>
                  <Input
                    id="customerName"
                    placeholder="Введите ваше имя"
                    value={deliveryInfo.customerName}
                    onChange={(e) => setDeliveryInfo(prev => ({ ...prev, customerName: e.target.value }))}
                  />
                </div>

                <div>
                  <Label htmlFor="customerPhone">Телефон *</Label>
                  <Input
                    id="customerPhone"
                    placeholder="+998 90 123 45 67"
                    value={deliveryInfo.customerPhone}
                    onChange={(e) => setDeliveryInfo(prev => ({ ...prev, customerPhone: e.target.value }))}
                  />
                </div>

                <div>
                  <Label htmlFor="address">Адрес доставки *</Label>
                  <div className="flex gap-2">
                    <Input
                      id="address"
                      placeholder="Введите адрес"
                      value={deliveryInfo.address}
                      onChange={(e) => setDeliveryInfo(prev => ({ ...prev, address: e.target.value }))}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddressSearch()}
                    />
                    <Button variant="outline" onClick={handleAddressSearch}>
                      <MapPin className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="rounded-lg overflow-hidden border border-border">
                  {mapError ? (
                    <div className="h-[250px] flex items-center justify-center bg-muted text-muted-foreground text-sm">
                      {mapError}
                    </div>
                  ) : (
                    <div
                      ref={mapContainerRef}
                      className="h-[250px] w-full"
                      style={{ minHeight: '250px' }}
                    />
                  )}
                </div>

                {deliveryInfo.lat && deliveryInfo.lng && (
                  <div className="text-xs text-muted-foreground flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    Координаты: {deliveryInfo.lat.toFixed(6)}, {deliveryInfo.lng.toFixed(6)}
                  </div>
                )}
              </div>

              <Button
                onClick={handleContinueToPayment}
                className="w-full mt-4"
                disabled={!isDeliveryValid}
              >
                Перейти к оплате
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-muted rounded-lg p-3 mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-muted-foreground">К оплате:</span>
                  <span className="text-xl font-bold text-primary">{formatPrice(total)}</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  Доставка: {deliveryInfo.address}
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="text-sm font-medium mb-2">Ваш заказ:</div>
                {items.map((item, index) => (
                  <div key={index} className="text-sm text-muted-foreground flex justify-between">
                    <span>{item.name} × {item.quantity}</span>
                    <span>{formatPrice(item.price * item.quantity)}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <div className="text-sm font-medium">Выберите способ оплаты:</div>

                {config?.payment?.click?.enabled !== false && (
                  <Button
                    variant="outline"
                    className="w-full h-14 justify-start gap-3 hover:border-primary"
                    onClick={() => handlePayment('click')}
                    disabled={isLoading}
                  >
                    {isLoading && selectedPayment === 'click' ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-[#00AEEF] flex items-center justify-center">
                        <span className="text-white font-bold text-xs">CLICK</span>
                      </div>
                    )}
                    <div className="text-left">
                      <div className="font-medium">Click</div>
                      <div className="text-xs text-muted-foreground">Оплата через Click</div>
                    </div>
                  </Button>
                )}

                {config?.payment?.payme?.enabled !== false && (
                  <Button
                    variant="outline"
                    className="w-full h-14 justify-start gap-3 hover:border-primary"
                    onClick={() => handlePayment('payme')}
                    disabled={isLoading}
                  >
                    {isLoading && selectedPayment === 'payme' ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-[#00CDBE] flex items-center justify-center">
                        <span className="text-white font-bold text-xs">Payme</span>
                      </div>
                    )}
                    <div className="text-left">
                      <div className="font-medium">Payme</div>
                      <div className="text-xs text-muted-foreground">Оплата через Payme</div>
                    </div>
                  </Button>
                )}

                {config?.payment?.uzum?.enabled !== false && (
                  <Button
                    variant="outline"
                    className="w-full h-14 justify-start gap-3 hover:border-primary"
                    onClick={() => handlePayment('uzum')}
                    disabled={isLoading}
                  >
                    {isLoading && selectedPayment === 'uzum' ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-[#7B68EE] flex items-center justify-center">
                        <span className="text-white font-bold text-xs">Uzum</span>
                      </div>
                    )}
                    <div className="text-left">
                      <div className="font-medium">Uzum Bank</div>
                      <div className="text-xs text-muted-foreground">Оплата через Uzum</div>
                    </div>
                  </Button>
                )}
              </div>

              <Button
                variant="ghost"
                onClick={() => setStep('delivery')}
                className="w-full mt-2"
              >
                ← Вернуться к адресу
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
