import { useConfig } from '@/hooks/useConfig'
import { useLayoutEffect } from 'react'

function hexToHSL(hex: string): string {
	hex = hex.replace(/^#/, '')

	const r = parseInt(hex.substring(0, 2), 16) / 255
	const g = parseInt(hex.substring(2, 4), 16) / 255
	const b = parseInt(hex.substring(4, 6), 16) / 255

	const max = Math.max(r, g, b)
	const min = Math.min(r, g, b)
	let h = 0,
		s = 0,
		l = (max + min) / 2

	if (max !== min) {
		const d = max - min
		s = l > 0.5 ? d / (2 - max - min) : d / (max + min)

		switch (max) {
			case r:
				h = ((g - b) / d + (g < b ? 6 : 0)) / 6
				break
			case g:
				h = ((b - r) / d + 2) / 6
				break
			case b:
				h = ((r - g) / d + 4) / 6
				break
		}
	}

	h = Math.round(h * 360)
	s = Math.round(s * 100)
	l = Math.round(l * 100)

	return `${h} ${s}% ${l}%`
}

import { useTheme } from '@/components/ThemeProvider'

// ... (keep helper functions)

export default function ThemeApplier() {
	const { config } = useConfig()
	const { theme } = useTheme()

	useLayoutEffect(() => {
		if (!config?.colorScheme) return

		const root = document.documentElement
		const isDark =
			theme === 'dark' ||
			(theme === 'system' &&
				window.matchMedia('(prefers-color-scheme: dark)').matches)

		// Apply colors based on theme
		const currentScheme =
			isDark && config.colorSchemeDark
				? config.colorSchemeDark
				: config.colorScheme

		// Common colors (always apply from chosen scheme)
		root.style.setProperty('--primary', hexToHSL(currentScheme.primary))
		root.style.setProperty(
			'--primary-foreground',
			hexToHSL(currentScheme.primaryForeground)
		)
		root.style.setProperty('--accent', hexToHSL(currentScheme.accent))
		root.style.setProperty(
			'--accent-foreground',
			hexToHSL(currentScheme.accentForeground)
		)

		// Surface and other colors
		root.style.setProperty('--background', hexToHSL(currentScheme.background))
		root.style.setProperty('--foreground', hexToHSL(currentScheme.foreground))
		root.style.setProperty('--card', hexToHSL(currentScheme.card))
		root.style.setProperty(
			'--card-foreground',
			hexToHSL(currentScheme.cardForeground)
		)
		root.style.setProperty('--secondary', hexToHSL(currentScheme.secondary))
		root.style.setProperty(
			'--secondary-foreground',
			hexToHSL(currentScheme.secondaryForeground)
		)
		root.style.setProperty('--muted', hexToHSL(currentScheme.muted))
		root.style.setProperty(
			'--muted-foreground',
			hexToHSL(currentScheme.mutedForeground)
		)
		root.style.setProperty('--border', hexToHSL(currentScheme.border))
		root.style.setProperty('--input', hexToHSL(currentScheme.input))
		root.style.setProperty('--ring', hexToHSL(currentScheme.ring))

		root.style.setProperty('--card-border', hexToHSL(currentScheme.border))
		root.style.setProperty('--sidebar', hexToHSL(currentScheme.card))
		root.style.setProperty(
			'--sidebar-foreground',
			hexToHSL(currentScheme.cardForeground)
		)
		root.style.setProperty('--sidebar-border', hexToHSL(currentScheme.border))
		root.style.setProperty('--sidebar-primary', hexToHSL(currentScheme.primary))
		root.style.setProperty(
			'--sidebar-primary-foreground',
			hexToHSL(currentScheme.primaryForeground)
		)
		root.style.setProperty('--sidebar-accent', hexToHSL(currentScheme.accent))
		root.style.setProperty(
			'--sidebar-accent-foreground',
			hexToHSL(currentScheme.accentForeground)
		)
		root.style.setProperty('--sidebar-ring', hexToHSL(currentScheme.ring))
	}, [config, theme])

	return null
}
