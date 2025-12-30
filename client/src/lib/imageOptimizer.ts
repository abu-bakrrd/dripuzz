/**
 * Утилита для оптимизации изображений Cloudinary
 * Автоматически выбирает оптимальный формат (AVIF/WebP) и размер
 */

export interface ImageSize {
	width?: number
	height?: number
}

export type ImageFormat = 'auto' | 'avif' | 'webp' | 'jpg' | 'png'

/**
 * Проверяет, является ли URL изображением Cloudinary
 */
export function isCloudinaryUrl(url: string): boolean {
	return url.includes('res.cloudinary.com') || url.includes('cloudinary.com')
}

/**
 * Оптимизирует URL изображения Cloudinary
 * 
 * @param url - Оригинальный URL изображения
 * @param options - Опции оптимизации
 * @returns Оптимизированный URL
 */
export function optimizeCloudinaryImage(
	url: string,
	options: {
		width?: number
		height?: number
		format?: ImageFormat
		quality?: number | 'auto'
		crop?: 'fill' | 'scale' | 'fit' | 'limit' | 'pad'
	} = {}
): string {
	// Если это не Cloudinary URL, возвращаем как есть
	if (!isCloudinaryUrl(url)) {
		return url
	}

	const {
		width,
		height,
		format = 'auto',
		quality = 'auto',
		crop = 'fill',
	} = options

	// Парсим URL Cloudinary
	// Формат: https://res.cloudinary.com/{cloud_name}/image/upload/{transformations}/{public_id}.{extension}
	const urlParts = url.split('/upload/')
	if (urlParts.length !== 2) {
		return url // Не удалось распарсить, возвращаем оригинал
	}

	const [base, rest] = urlParts
	
	// Если в URL уже есть трансформации (начинается с w_, h_, c_, f_, q_ и т.д.), удаляем их
	// Формат трансформаций: w_100,h_100,c_fill,f_auto,q_auto/...
	let publicIdPath = rest
	const firstSlashIndex = rest.indexOf('/')
	if (firstSlashIndex > 0) {
		const firstPart = rest.substring(0, firstSlashIndex)
		// Проверяем, является ли первая часть трансформациями (содержит параметры вида w_, h_, c_ и т.д.)
		if (/^[whcgfqa]_/.test(firstPart) || firstPart.includes(',')) {
			// Это трансформации, берем часть после первого слеша
			publicIdPath = rest.substring(firstSlashIndex + 1)
		}
	}

	// Собираем трансформации
	const transformations: string[] = []

	// Размеры
	if (width || height) {
		const sizeStr = width && height 
			? `w_${width},h_${height}`
			: width 
			? `w_${width}`
			: `h_${height}`
		transformations.push(sizeStr)
	}

	// Кроп
	transformations.push(`c_${crop}`)

	// Формат (автовыбор AVIF/WebP)
	if (format === 'auto') {
		// Cloudinary автоматически выберет лучший формат (AVIF, затем WebP, затем оригинал)
		transformations.push('f_auto')
	} else {
		transformations.push(`f_${format}`)
	}

	// Качество
	if (quality === 'auto') {
		transformations.push('q_auto')
	} else {
		transformations.push(`q_${quality}`)
	}

	// Собираем URL
	const transformString = transformations.join(',')
	return `${base}/upload/${transformString}/${publicIdPath}`
}

/**
 * Оптимизирует изображение для карточки товара (thumbnail)
 */
export function optimizeProductThumbnail(url: string): string {
	// Для карточек товаров используем размер 400x400px
	// На мобильных устройствах обычно максимум 400px ширина
	return optimizeCloudinaryImage(url, {
		width: 400,
		height: 400,
		format: 'auto',
		quality: 'auto',
		crop: 'fill',
	})
}

/**
 * Оптимизирует изображение для детального просмотра товара
 */
export function optimizeProductDetail(url: string): string {
	// Для детального просмотра используем размер 800x800px
	// Максимальная ширина экрана ~420px, но для Retina дисплеев нужен x2
	return optimizeCloudinaryImage(url, {
		width: 800,
		height: 800,
		format: 'auto',
		quality: 'auto',
		crop: 'fill',
	})
}

/**
 * Оптимизирует изображение для первого экрана (приоритетная загрузка)
 */
export function optimizeProductHero(url: string): string {
	// Для героических изображений используем размер 600x600px
	// Баланс между качеством и размером файла
	return optimizeCloudinaryImage(url, {
		width: 600,
		height: 600,
		format: 'auto',
		quality: 'auto',
		crop: 'fill',
	})
}

/**
 * Генерирует srcset для responsive изображений
 */
export function generateSrcSet(
	url: string,
	widths: number[] = [400, 600, 800, 1200]
): string {
	if (!isCloudinaryUrl(url)) {
		return url
	}

	return widths
		.map((width) => {
			const optimizedUrl = optimizeCloudinaryImage(url, {
				width,
				height: width,
				format: 'auto',
				quality: 'auto',
				crop: 'fill',
			})
			return `${optimizedUrl} ${width}w`
		})
		.join(', ')
}

/**
 * Генерирует sizes атрибут для responsive изображений
 */
export function generateSizes(defaultSize: string = '400px'): string {
	return `(max-width: 420px) 400px, ${defaultSize}`
}
