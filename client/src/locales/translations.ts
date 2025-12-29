/**
 * Translations for the frontend
 * Переводы для фронтенда
 */

export interface Translations {
	[key: string]: string
}

export const translations: Record<string, Translations> = {
	ru: {
		// General
		loading: 'Загрузка...',
		error: 'Ошибка',
		success: 'Успешно',
		cancel: 'Отмена',
		save: 'Сохранить',
		delete: 'Удалить',
		edit: 'Редактировать',
		search: 'Поиск',
		filter: 'Фильтр',
		sort: 'Сортировка',
		all: 'Все',
		yes: 'Да',
		no: 'Нет',

		// Navigation
		home: 'Главная',
		catalog: 'Каталог',
		cart: 'Корзина',
		favorites: 'Избранное',
		orders: 'Заказы',
		profile: 'Профиль',
		account: 'Аккаунт',
		logout: 'Выйти',
		login: 'Войти',
		register: 'Регистрация',

		// Product
		product: 'Товар',
		products: 'Товары',
		price: 'Цена',
		description: 'Описание',
		category: 'Категория',
		categories: 'Категории',
		inStock: 'В наличии',
		outOfStock: 'Нет в наличии',
		addToCart: 'Добавить в корзину',
		addedToCart: 'Добавлено в корзину',
		buyNow: 'Купить сейчас',
		selectColor: 'Выберите цвет',
		selectSize: 'Выберите размер',
		colors: 'Цвета',
		sizes: 'Размеры',

		// Cart
		yourCart: 'Ваша корзина',
		emptyCart: 'Корзина пуста',
		cartTotal: 'Итого',
		subtotal: 'Подытог',
		total: 'Итого',
		quantity: 'Количество',
		remove: 'Удалить',
		clearCart: 'Очистить корзину',
		continueShopping: 'Продолжить покупки',
		checkout: 'Оформить заказ',
		proceedToCheckout: 'Перейти к оформлению',

		// Favorites
		yourFavorites: 'Ваше избранное',
		emptyFavorites: 'Нет избранных товаров',
		addToFavorites: 'Добавить в избранное',
		removeFromFavorites: 'Удалить из избранного',

		// Checkout
		checkoutTitle: 'Оформление заказа',
		deliveryAddress: 'Адрес доставки',
		customerName: 'Имя',
		customerPhone: 'Телефон',
		paymentMethod: 'Способ оплаты',
		placeOrder: 'Оформить заказ',
		orderPlaced: 'Заказ оформлен',
		orderNumber: 'Номер заказа',

		// Payment methods
		paymentClick: 'Click',
		paymentPayme: 'Payme',
		paymentUzum: 'Uzum Bank',
		paymentCardTransfer: 'Перевод на карту',

		// Order statuses
		statusPending: 'Ожидает оплаты',
		statusReviewing: 'Рассматривается',
		statusPaid: 'Оплачен',
		statusProcessing: 'Собирается',
		statusShipped: 'В пути',
		statusDelivered: 'Доставлен',
		statusCancelled: 'Отменён',

		// Auth
		email: 'Email',
		password: 'Пароль',
		confirmPassword: 'Подтвердите пароль',
		forgotPassword: 'Забыли пароль?',
		resetPassword: 'Сбросить пароль',
		createAccount: 'Создать аккаунт',
		haveAccount: 'Уже есть аккаунт?',
		noAccount: 'Нет аккаунта?',
		signIn: 'Войти',
		signUp: 'Зарегистрироваться',
		signOut: 'Выйти',

		// Sort options
		sortNew: 'Новые',
		sortPriceAsc: 'Дешевле',
		sortPriceDesc: 'Дороже',
		sortPopular: 'Популярные',

		// Filters
		priceRange: 'Диапазон цен',
		minPrice: 'Мин. цена',
		maxPrice: 'Макс. цена',
		applyFilters: 'Применить',
		resetFilters: 'Сбросить',

		// Messages
		itemAddedToCart: 'Товар добавлен в корзину',
		itemRemovedFromCart: 'Товар удален из корзины',
		cartCleared: 'Корзина очищена',
		orderSuccess: 'Заказ успешно оформлен!',
		orderError: 'Ошибка при оформлении заказа',
		loginRequired: 'Необходимо войти в систему',
		loginSuccess: 'Вы успешно вошли',
		registerSuccess: 'Регистрация успешна',
		logoutSuccess: 'Вы вышли из системы',

		// Delivery
		delivery: 'Доставка',
		deliveryFree: 'Бесплатная доставка',
		deliveryNote: 'Доставка оплачивается при получении',

		// Contact
		contactManager: 'Связаться с менеджером',
		manager: 'Менеджер',
	},

	en: {
		// General
		loading: 'Loading...',
		error: 'Error',
		success: 'Success',
		cancel: 'Cancel',
		save: 'Save',
		delete: 'Delete',
		edit: 'Edit',
		search: 'Search',
		filter: 'Filter',
		sort: 'Sort',
		all: 'All',
		yes: 'Yes',
		no: 'No',

		// Navigation
		home: 'Home',
		catalog: 'Catalog',
		cart: 'Cart',
		favorites: 'Favorites',
		orders: 'Orders',
		profile: 'Profile',
		account: 'Account',
		logout: 'Logout',
		login: 'Login',
		register: 'Register',

		// Product
		product: 'Product',
		products: 'Products',
		price: 'Price',
		description: 'Description',
		category: 'Category',
		categories: 'Categories',
		inStock: 'In Stock',
		outOfStock: 'Out of Stock',
		addToCart: 'Add to Cart',
		addedToCart: 'Added to Cart',
		buyNow: 'Buy Now',
		selectColor: 'Select Color',
		selectSize: 'Select Size',
		colors: 'Colors',
		sizes: 'Sizes',

		// Cart
		yourCart: 'Your Cart',
		emptyCart: 'Cart is Empty',
		cartTotal: 'Total',
		subtotal: 'Subtotal',
		total: 'Total',
		quantity: 'Quantity',
		remove: 'Remove',
		clearCart: 'Clear Cart',
		continueShopping: 'Continue Shopping',
		checkout: 'Checkout',
		proceedToCheckout: 'Proceed to Checkout',

		// Favorites
		yourFavorites: 'Your Favorites',
		emptyFavorites: 'No Favorite Items',
		addToFavorites: 'Add to Favorites',
		removeFromFavorites: 'Remove from Favorites',

		// Checkout
		checkoutTitle: 'Checkout',
		deliveryAddress: 'Delivery Address',
		customerName: 'Name',
		customerPhone: 'Phone',
		paymentMethod: 'Payment Method',
		placeOrder: 'Place Order',
		orderPlaced: 'Order Placed',
		orderNumber: 'Order Number',

		// Payment methods
		paymentClick: 'Click',
		paymentPayme: 'Payme',
		paymentUzum: 'Uzum Bank',
		paymentCardTransfer: 'Card Transfer',

		// Order statuses
		statusPending: 'Pending Payment',
		statusReviewing: 'Under Review',
		statusPaid: 'Paid',
		statusProcessing: 'Processing',
		statusShipped: 'Shipped',
		statusDelivered: 'Delivered',
		statusCancelled: 'Cancelled',

		// Auth
		email: 'Email',
		password: 'Password',
		confirmPassword: 'Confirm Password',
		forgotPassword: 'Forgot Password?',
		resetPassword: 'Reset Password',
		createAccount: 'Create Account',
		haveAccount: 'Already have an account?',
		noAccount: "Don't have an account?",
		signIn: 'Sign In',
		signUp: 'Sign Up',
		signOut: 'Sign Out',

		// Sort options
		sortNew: 'New',
		sortPriceAsc: 'Price: Low to High',
		sortPriceDesc: 'Price: High to Low',
		sortPopular: 'Popular',

		// Filters
		priceRange: 'Price Range',
		minPrice: 'Min Price',
		maxPrice: 'Max Price',
		applyFilters: 'Apply',
		resetFilters: 'Reset',

		// Messages
		itemAddedToCart: 'Item added to cart',
		itemRemovedFromCart: 'Item removed from cart',
		cartCleared: 'Cart cleared',
		orderSuccess: 'Order placed successfully!',
		orderError: 'Error placing order',
		loginRequired: 'Login required',
		loginSuccess: 'Successfully logged in',
		registerSuccess: 'Registration successful',
		logoutSuccess: 'Logged out',

		// Delivery
		delivery: 'Delivery',
		deliveryFree: 'Free Delivery',
		deliveryNote: 'Delivery paid on receipt',

		// Contact
		contactManager: 'Contact Manager',
		manager: 'Manager',
	},
}

export function getTranslation(key: string, language: string = 'ru'): string {
	if (!translations[language]) {
		language = 'ru'
	}

	return translations[language][key] || key
}

export function getAllTranslations(language: string = 'ru'): Translations {
	if (!translations[language]) {
		language = 'ru'
	}

	return translations[language]
}
