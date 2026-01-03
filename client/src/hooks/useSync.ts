import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

export function useSync() {
	const queryClient = useQueryClient()
	const lastVersion = useRef<number | null>(null)
	const intervalRef = useRef<NodeJS.Timeout | null>(null)

	useEffect(() => {
		const checkVersion = async () => {
			try {
				const response = await fetch('/api/config/version')
				if (response.ok) {
					const { version } = await response.json()

					if (lastVersion.current !== null && version > lastVersion.current) {
						// Version increased, invalidate all relevant queries
						queryClient.invalidateQueries({ queryKey: ['/api/categories'] })
						queryClient.invalidateQueries({ queryKey: ['/api/products'] })
						queryClient.invalidateQueries({ queryKey: ['/api/config'] })
						// Also invalidate specific product details if any are open
						// queryClient.invalidateQueries({ queryKey: [/^\/api\/products\//] })
					}

					lastVersion.current = version
				}
			} catch (error) {
				console.error('Sync check failed:', error)
			}
		}

		// Initial check
		checkVersion()

		// Poll every 10 seconds
		intervalRef.current = setInterval(checkVersion, 10000)

		return () => {
			if (intervalRef.current) {
				clearInterval(intervalRef.current)
			}
		}
	}, [queryClient])

	return null
}
