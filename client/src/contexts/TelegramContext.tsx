import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { retrieveLaunchParams } from '@telegram-apps/sdk';

interface TelegramUser {
  id: string;
  telegram_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
}

interface TelegramContextType {
  user: TelegramUser | null;
  isLoading: boolean;
  telegramData: any;
}

const TelegramContext = createContext<TelegramContextType>({
  user: null,
  isLoading: true,
  telegramData: null,
});

export const useTelegram = () => useContext(TelegramContext);

interface TelegramProviderProps {
  children: ReactNode;
}

export function TelegramProvider({ children }: TelegramProviderProps) {
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [telegramData, setTelegramData] = useState<any>(null);

  useEffect(() => {
    const initTelegram = async () => {
      try {
        let telegramUser: { id: number; username?: string; firstName?: string; lastName?: string } | null = null;

        // Initialize Telegram WebApp if available
        if (window.Telegram?.WebApp) {
          window.Telegram.WebApp.ready();
        }

        // Method 1: Try standard Telegram WebApp API first
        if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
          const tgUser = window.Telegram.WebApp.initDataUnsafe.user;
          telegramUser = {
            id: tgUser.id,
            username: tgUser.username,
            firstName: tgUser.first_name,
            lastName: tgUser.last_name,
          };
          console.log('🔵 Got Telegram data from WebApp.initDataUnsafe');
        } else {
          // Method 2: Fallback to retrieveLaunchParams
          try {
            const { initData } = retrieveLaunchParams();
            const userData = (initData as any)?.user;
            if (userData) {
              telegramUser = userData;
              console.log('🔵 Got Telegram data from retrieveLaunchParams');
            }
          } catch (launchParamsError) {
            console.log('⚠️ retrieveLaunchParams failed, not in Telegram:', launchParamsError);
          }
        }
        
        if (telegramUser) {
          setTelegramData(telegramUser);
          
          console.log('🔵 TELEGRAM USER DATA:', {
            source: 'Telegram Mini App',
            telegram_id: telegramUser.id,
            username: telegramUser.username,
            first_name: telegramUser.firstName,
            last_name: telegramUser.lastName,
          });
          
          // Authenticate with backend
          const response = await fetch('/api/auth/telegram', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              telegram_id: telegramUser.id,
              username: telegramUser.username,
              first_name: telegramUser.firstName,
              last_name: telegramUser.lastName,
            }),
          });

          if (response.ok) {
            const data = await response.json();
            console.log('✅ AUTH SUCCESS (Telegram):', {
              user_id: data.user.id,
              telegram_id: data.user.telegram_id,
              is_new_user: data.is_new,
              username: data.user.username,
            });
            setUser(data.user);
          } else {
            console.error('❌ Backend authentication failed:', await response.text());
          }
        } else {
          console.log('❌ Not running in Telegram mini app');
        }
      } catch (error) {
        console.error('🔴 Telegram init error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initTelegram();
  }, []);

  return (
    <TelegramContext.Provider value={{ user, isLoading, telegramData }}>
      {children}
    </TelegramContext.Provider>
  );
}
