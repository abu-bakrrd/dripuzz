import re

def test_search_logic(user_question):
    print(f"🔹 Входящий вопрос: '{user_question}'")
    
    # 1. Нормализация (как в боте)
    # кириллица -> латиница, убираем #
    clean_question = user_question.lower().replace('#', '').translate(str.maketrans("асеорх", "aceopx"))
    print(f"🔹 После нормализации: '{clean_question}'")

    # 2. Regex паттерны (как в боте)
    # Полный UUID: 8-4-4-4-12
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    # Короткий ID: 6+ hex символов
    short_id_pattern = r'\b[0-9a-f]{6,}\b' # Здесь \b важен!

    found_uuids = re.findall(uuid_pattern, clean_question)
    print(f"🧐 Поиск полного UUID: {found_uuids}")

    if not found_uuids:
        found_uuids = re.findall(short_id_pattern, clean_question)
        print(f"🧐 Поиск короткого ID (fallback): {found_uuids}")

    if found_uuids:
        extracted_id = found_uuids[0]
        print(f"✅ УСПЕХ! Извлеченный ID: '{extracted_id}'")
        
        # Эмуляция проверки на "правильность" UUID
        parts = extracted_id.split('-')
        if len(parts) == 5:
            print(f"📊 Структура UUID: {[len(p) for p in parts]}")
            if len(parts[0]) != 8:
                print("⚠️ ВНИМАНИЕ: Первая часть UUID не равна 8 символам! В стандартном UUID это 8 символов.")
                print("   Возможно, в ID закралась лишняя цифра?")
    else:
        print("❌ ID не найден в тексте.")

if __name__ == "__main__":
    # Тест 1: ID из чата (с возможной опечаткой fаc35e1b7 -> 9 символов)
    print("--- ТЕСТ 1 (Ваш пример) ---")
    test_search_logic("посмотри какой статус у моего заказа а fаc35e1b7-ac7d-4770-ac34-04c120d22afb")
    
    # Тест 2: Стандартный UUID (8 символов в начале)
    print("\n--- ТЕСТ 2 (Правильный UUID) ---")
    test_search_logic("Check order fac35e1b-ac7d-4770-ac34-04c120d22afb")
    
    # Тест 3: С хештегом и кириллицей
    print("\n--- ТЕСТ 3 (С мусором) ---")
    test_search_logic("Где заказ #fаc35e1b ???")
