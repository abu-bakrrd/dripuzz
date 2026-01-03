import { createContext, useContext, useLayoutEffect, useState } from 'react'

type Theme = 'dark' | 'light' | 'system'

type ThemeProviderProps = {
	children: React.ReactNode
	defaultTheme?: Theme
	storageKey?: string
}

type ThemeProviderState = {
	theme: Theme
	setTheme: (theme: Theme) => void
}

const initialState: ThemeProviderState = {
	theme: 'system',
	setTheme: () => null,
}

const ThemeProviderContext = createContext<ThemeProviderState>(initialState)

export function ThemeProvider({
	children,
	defaultTheme = 'system',
	storageKey = 'vite-ui-theme',
	...props
}: ThemeProviderProps) {
	const [theme, setTheme] = useState<Theme>(() => {
		return (localStorage.getItem(storageKey) as Theme) || defaultTheme
	})

	useLayoutEffect(() => {
		const root = window.document.documentElement

		// Добавляем класс для мгновенного переключения (без анимаций)
		root.classList.add('no-transitions')

		// Синхронное переключение темы
		root.classList.remove('light', 'dark')

		if (theme === 'system') {
			const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
				.matches
				? 'dark'
				: 'light'

			root.classList.add(systemTheme)
		} else {
			root.classList.add(theme)
		}

		// Принудительно вызываем перерисовку (reflow) чтобы изменения применились мгновенно
		window.getComputedStyle(root).opacity

		// Удаляем класс после завершения синхронного цикла обновлений
		const timeout = setTimeout(() => {
			root.classList.remove('no-transitions')
		}, 0)

		return () => clearTimeout(timeout)
	}, [theme])

	const value = {
		theme,
		setTheme: (theme: Theme) => {
			// Добавляем класс сразу при клике, чтобы даже начало смены было мгновенным
			document.documentElement.classList.add('no-transitions')
			localStorage.setItem(storageKey, theme)
			setTheme(theme)
		},
	}

	return (
		<ThemeProviderContext.Provider value={value} {...props}>
			{children}
		</ThemeProviderContext.Provider>
	)
}

export const useTheme = () => {
	const context = useContext(ThemeProviderContext)

	if (context === undefined)
		throw new Error('useTheme must be used within a ThemeProvider')

	return context
}
