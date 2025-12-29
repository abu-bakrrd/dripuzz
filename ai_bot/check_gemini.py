import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def check_gemini():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ ОШИБКА: GEMINI_API_KEY не найден в .env")
        return

    print(f"🔑 Проверка API ключа: {api_key[:5]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)

    print("\n🔍 Список доступных моделей для вашего ключа:")
    print("-" * 50)
    
    try:
        available_models = genai.list_models()
        count = 0
        for m in available_models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name} (Поддерживает чат)")
                count += 1
            else:
                print(f"➖ {m.name}")
        
        if count == 0:
            print("\n⚠️ Предупреждение: Не найдено моделей, поддерживающих 'generateContent'.")
        else:
            print(f"\n✨ Найдено {count} подходящих моделей.")
            
    except Exception as e:
        print(f"\n❌ Ошибка при получении списка моделей: {e}")
        print("\nВозможные причины:")
        print("1. Ключ API недействителен или скопирован не полностью.")
        print("2. Вы находитесь в регионе, где Gemini API ограничен (например, некоторые страны ЕС).")
        print("3. Проблемы с интернет-соединением или VPN.")

if __name__ == "__main__":
    check_gemini()
