/**
 * React hook for translations
 * React хук для переводов
 */

import { getAllTranslations, getTranslation } from '@/locales/translations'
import { useConfig } from './useConfig'

export function useTranslation() {
	const { config } = useConfig()

	// Get language from config, default to "ru"
	const language = config?.language || 'ru'

	/**
	 * Get translation by key
	 * Получить перевод по ключу
	 */
	const t = (key: string): string => {
		return getTranslation(key, language)
	}

	/**
	 * Get all translations for current language
	 * Получить все переводы для текущего языка
	 */
	const translations = getAllTranslations(language)

	return {
		t,
		language,
		translations,
	}
}
