import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAuth } from '@/contexts/AuthContext'
import { MessageCircle, Search, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

interface ChatUser {
	id: string
	first_name: string
	last_name: string
	email: string
	phone: string
	last_message: string
	last_message_time: string
	unread_count: number
}

interface Message {
	id: string
	content: string
	sender_id: string
	created_at: string
	is_read: boolean
	sender_name?: string
}

export default function AdminChat() {
	const { user } = useAuth()
	const [users, setUsers] = useState<ChatUser[]>([])
	const [selectedUserId, setSelectedUserId] = useState<string | null>(null)
	const [messages, setMessages] = useState<Message[]>([])
	const [inputValue, setInputValue] = useState('')
	const [ws, setWs] = useState<WebSocket | null>(null)
	const [isConnected, setIsConnected] = useState(false) // eslint-disable-line @typescript-eslint/no-unused-vars
	const scrollRef = useRef<HTMLDivElement>(null)
	const [searchQuery, setSearchQuery] = useState('')

	// Fetch user list
	const fetchUsers = async () => {
		try {
			const res = await fetch('/api/admin/chat/list')
			if (res.ok) {
				const data = await res.json()
				setUsers(data)
			}
		} catch (err) {
			console.error('Failed to load chat users:', err)
		}
	}

	useEffect(() => {
		fetchUsers()
		const interval = setInterval(fetchUsers, 30000) // Poll every 30s as backup
		return () => clearInterval(interval)
	}, [])

	// WebSocket connection
	useEffect(() => {
		if (!user) return

		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
		const wsUrl = `${protocol}//${window.location.host}/ws?userId=${user.id}&isAdmin=true`
		const socket = new WebSocket(wsUrl)

		socket.onopen = () => {
			console.log('Admin connected to chat')
			setIsConnected(true)
			setWs(socket)
		}

		socket.onmessage = event => {
			try {
				const data = JSON.parse(event.data)
				if (data.type === 'new_message') {
					const msg = data.message

					// If message is for currently selected user, add it to list
					if (
						selectedUserId &&
						(msg.sender_id === selectedUserId || msg.user_id === selectedUserId)
					) {
						setMessages(prev => [...prev, msg])
						// Mark as read if from user
						if (msg.sender_id === selectedUserId) {
							markAsRead(selectedUserId)
						}
					}

					// Always refresh user list to update last message/unread count
					fetchUsers()
				}
			} catch (e) {
				console.error('Error parsing WS message:', e)
			}
		}

		socket.onclose = () => {
			console.log('Admin disconnected from chat')
			setIsConnected(false)
			setWs(null)
		}

		return () => {
			socket.close()
		}
	}, [user, selectedUserId])

	// Load messages when user selected
	useEffect(() => {
		if (selectedUserId) {
			setMessages([]) // Clear previous
			fetch(`/api/admin/chat/${selectedUserId}`)
				.then(res => res.json())
				.then(data => {
					// Response format: { user: {...}, messages: [...] }
					if (data.messages && Array.isArray(data.messages)) {
						setMessages(data.messages)
						markAsRead(selectedUserId)
					}
				})
				.catch(err => console.error('Failed to load messages:', err))
		}
	}, [selectedUserId])

	const markAsRead = async (senderId: string) => {
		try {
			await fetch('/api/chat/read', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ userId: user?.id, senderId: senderId }),
			})
			// Update local state to reflect read status (optional, but good for UI)
			setUsers(prev =>
				prev.map(u => (u.id === senderId ? { ...u, unread_count: 0 } : u))
			)
		} catch (e) {
			console.error('Failed to mark read:', e)
		}
	}

	// Auto-scroll to bottom
	useEffect(() => {
		if (scrollRef.current) {
			scrollRef.current.scrollIntoView({ behavior: 'smooth' })
		}
	}, [messages])

	const handleSend = () => {
		if (!inputValue.trim() || !ws || !selectedUserId) return

		const message = {
			type: 'message',
			content: inputValue,
			recipientId: selectedUserId,
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

	const filteredUsers = users.filter(
		u =>
			(u.first_name + ' ' + u.last_name)
				.toLowerCase()
				.includes(searchQuery.toLowerCase()) ||
			u.email?.toLowerCase().includes(searchQuery.toLowerCase())
	)

	return (
		<div className='grid grid-cols-1 md:grid-cols-3 gap-4 h-[calc(100vh-140px)]'>
			{/* Sidebar: User List */}
			<Card className='col-span-1 flex flex-col overflow-hidden'>
				<div className='p-4 border-b'>
					<div className='relative'>
						<Search className='absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground' />
						<Input
							placeholder='Поиск пользователей...'
							className='pl-8'
							value={searchQuery}
							onChange={e => setSearchQuery(e.target.value)}
						/>
					</div>
				</div>
				<ScrollArea className='flex-1'>
					{filteredUsers.length === 0 ? (
						<div className='p-8 text-center text-muted-foreground'>
							Нет диалогов
						</div>
					) : (
						<div className='divide-y'>
							{filteredUsers.map(chatUser => (
								<div
									key={chatUser.id}
									onClick={() => setSelectedUserId(chatUser.id)}
									className={`p-4 cursor-pointer hover:bg-muted/50 transition-colors ${
										selectedUserId === chatUser.id ? 'bg-muted' : ''
									}`}
								>
									<div className='flex justify-between items-start mb-1'>
										<h3 className='font-semibold truncate pr-2'>
											{chatUser.first_name} {chatUser.last_name}
										</h3>
										{chatUser.last_message_time && (
											<span className='text-xs text-muted-foreground whitespace-nowrap'>
												{new Date(
													chatUser.last_message_time
												).toLocaleDateString()}
											</span>
										)}
									</div>
									<div className='flex justify-between items-center'>
										<p className='text-sm text-muted-foreground truncate max-w-[80%]'>
											{chatUser.last_message || 'Нет сообщений'}
										</p>
										{chatUser.unread_count > 0 && (
											<span className='inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs font-medium'>
												{chatUser.unread_count}
											</span>
										)}
									</div>
									<div className='mt-1 text-xs text-muted-foreground/50 truncate'>
										{chatUser.email}
									</div>
								</div>
							))}
						</div>
					)}
				</ScrollArea>
			</Card>

			{/* Main: Chat Area */}
			<Card className='col-span-1 md:col-span-2 flex flex-col overflow-hidden'>
				{selectedUserId ? (
					<>
						<div className='p-4 border-b flex justify-between items-center bg-muted/20'>
							<div>
								<div className='flex items-center gap-2'>
									<h3 className='font-semibold'>
										{users.find(u => u.id === selectedUserId)?.first_name}{' '}
										{users.find(u => u.id === selectedUserId)?.last_name}
									</h3>
									<span className='text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary'>
										Client
									</span>
								</div>
								<div className='flex flex-col text-xs text-muted-foreground mt-1'>
									<span>{users.find(u => u.id === selectedUserId)?.email}</span>
									<span>{users.find(u => u.id === selectedUserId)?.phone}</span>
								</div>
							</div>
						</div>

						<ScrollArea className='flex-1 p-4'>
							<div className='space-y-4'>
								{messages.map((msg, index) => {
									const isMe = msg.sender_id === user?.id // I am admin
									return (
										<div
											key={msg.id || index}
											className={`flex ${
												isMe ? 'justify-end' : 'justify-start'
											}`}
										>
											<div
												className={`max-w-[70%] rounded-2xl px-4 py-3 ${
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
						</ScrollArea>

						<div className='p-4 border-t bg-background'>
							<div className='flex gap-2'>
								<Input
									value={inputValue}
									onChange={e => setInputValue(e.target.value)}
									onKeyDown={handleKeyPress}
									placeholder='Напишите ответ...'
									className='flex-1'
								/>
								<Button
									onClick={handleSend}
									disabled={!inputValue.trim()}
									size='icon'
								>
									<Send className='h-4 w-4' />
								</Button>
							</div>
						</div>
					</>
				) : (
					<div className='flex-1 flex flex-col items-center justify-center text-muted-foreground'>
						<MessageCircle className='h-16 w-16 mb-4 opacity-20' />
						<p>Выберите чат из списка слева</p>
					</div>
				)}
			</Card>
		</div>
	)
}
