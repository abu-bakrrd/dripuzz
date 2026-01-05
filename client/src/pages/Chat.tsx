import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/contexts/AuthContext'
import { useConfig } from '@/hooks/useConfig'
import { ArrowLeft, Loader2, Send } from 'lucide-react' // Changed to Loader2 which is standard
import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'wouter'

interface Message {
	id: string
	content: string
	sender_id: string
	created_at: string
	is_read: boolean
}

export default function Chat() {
	const { user, isLoading } = useAuth()
	const { config } = useConfig()
	const [, setLocation] = useLocation()
	const [messages, setMessages] = useState<Message[]>([])
	const [inputValue, setInputValue] = useState('')
	const [ws, setWs] = useState<WebSocket | null>(null)
	const [isConnected, setIsConnected] = useState(false)
	const scrollRef = useRef<HTMLDivElement>(null)

	useEffect(() => {
		if (!isLoading && !user) {
			setLocation('/login')
		}
	}, [user, isLoading, setLocation])

	// Fetch initial messages
	useEffect(() => {
		if (user) {
			fetch(`/api/chat/messages?userId=${user.id}`)
				.then(res => res.json())
				.then(data => {
					if (Array.isArray(data)) {
						setMessages(data)
					}
				})
				.catch(err => console.error('Failed to load messages:', err))
		}
	}, [user])

	// WebSocket connection
	useEffect(() => {
		if (!user) return

		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
		const wsUrl = `${protocol}//${window.location.host}/ws?userId=${user.id}`
		const socket = new WebSocket(wsUrl)

		socket.onopen = () => {
			console.log('Connected to chat')
			setIsConnected(true)
			setWs(socket)
		}

		socket.onmessage = event => {
			try {
				const data = JSON.parse(event.data)
				if (data.type === 'new_message') {
					setMessages(prev => [...prev, data.message])
				}
			} catch (e) {
				console.error('Error parsing WS message:', e)
			}
		}

		socket.onclose = () => {
			console.log('Disconnected from chat')
			setIsConnected(false)
			setWs(null)
			// Reconnection logic could be added here
		}

		return () => {
			socket.close()
		}
	}, [user])

	// Auto-scroll to bottom
	useEffect(() => {
		if (scrollRef.current) {
			scrollRef.current.scrollIntoView({ behavior: 'smooth' })
		}
	}, [messages])

	const handleSend = () => {
		if (!inputValue.trim() || !ws || !user) return

		const message = {
			type: 'message',
			content: inputValue,
			recipientId: config?.managerContact, // Ideally this would be a specific admin ID, but for now we broadcast to admins
			// Note: In our WS server logic, if we are a USER, we don't strictly need recipientId as it goes to all admins
			// But good to keep format consistent
		}

		ws.send(JSON.stringify(message))
		setInputValue('')
	}

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault()
			handleSend()
		}
	}

	if (isLoading) {
		return (
			<div className='min-h-screen flex items-center justify-center'>
				<Loader2 className='h-8 w-8 animate-spin text-primary' />
			</div>
		)
	}

	return (
		<div className='min-h-screen bg-background flex flex-col'>
			{/* Header */}
			<div className='bg-background border-b border-border p-4 flex items-center gap-4 sticky top-0 z-10 shadow-sm'>
				<Button
					variant='ghost'
					size='icon'
					onClick={() => setLocation('/')}
					className='shrink-0'
				>
					<ArrowLeft className='h-5 w-5' />
				</Button>
				<div className='flex items-center gap-3'>
					<div className='w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-lg'>
						{config?.shopName?.charAt(0) || 'S'}
					</div>
					<div>
						<h1 className='font-semibold text-foreground'>
							{config?.shopName || 'Support'}
						</h1>
						<p className='text-xs text-muted-foreground'>
							{isConnected ? 'В сети' : 'Подключение...'}
						</p>
					</div>
				</div>
			</div>

			{/* Messages Area */}
			<div className='flex-1 p-4 pb-20'>
				{' '}
				{/* Added padding-bottom for mobile input clearance */}
				<div className='max-w-3xl mx-auto space-y-4'>
					{messages.length === 0 && (
						<div className='text-center text-muted-foreground py-10'>
							<p>Напишите нам, если у вас есть вопросы!</p>
						</div>
					)}
					{messages.map((msg, index) => {
						const isMe = msg.sender_id === user?.id
						return (
							<div
								key={msg.id || index}
								className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}
							>
								<div
									className={`max-w-[80%] rounded-2xl px-4 py-3 ${
										isMe
											? 'bg-primary text-primary-foreground rounded-br-none'
											: 'bg-muted text-foreground rounded-bl-none'
									}`}
								>
									<p className='text-sm whitespace-pre-wrap break-words'>
										{msg.content}
									</p>
									<p className={`text-[10px] mt-1 text-right opacity-70`}>
										{new Date(msg.created_at).toLocaleTimeString([], {
											hour: '2-digit',
											minute: '2-digit',
										})}
									</p>
								</div>
							</div>
						)
					})}
					<div ref={scrollRef} />
				</div>
			</div>

			{/* Input Area */}
			<div className='p-4 bg-background border-t border-border sticky bottom-0 container mx-auto'>
				<div className='max-w-3xl mx-auto flex gap-2'>
					<Input
						value={inputValue}
						onChange={e => setInputValue(e.target.value)}
						onKeyDown={handleKeyPress}
						placeholder='Введите сообщение...'
						className='flex-1'
						disabled={!isConnected}
					/>
					<Button
						onClick={handleSend}
						disabled={!inputValue.trim() || !isConnected}
						size='icon'
					>
						<Send className='h-4 w-4' />
					</Button>
				</div>
			</div>
		</div>
	)
}
