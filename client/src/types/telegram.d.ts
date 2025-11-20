declare global {
  interface Window {
    Telegram?: TelegramNamespace.Telegram;
  }

  namespace TelegramNamespace {
    interface Telegram {
      WebApp?: TelegramWebApp;
    }

    interface TelegramWebApp {
      initDataUnsafe?: TelegramWebAppInitData;
      initData?: string;
      ready: () => void;
    }

    interface TelegramWebAppInitData {
      user?: TelegramWebAppUser;
    }

    interface TelegramWebAppUser {
      id: number;
      username?: string;
      first_name?: string;
      last_name?: string;
      language_code?: string;
      photo_url?: string;
    }
  }
}

export {};
