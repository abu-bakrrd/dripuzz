import { spawn } from 'child_process'
import express from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { log, setupVite } from './vite'

const app = express()

// Flask will run on port 5001
const FLASK_PORT = 5001
const SERVER_PORT =
	process.env.SKIP_FLASK === 'true'
		? process.env.CHAT_PORT
			? parseInt(process.env.CHAT_PORT)
			: 5002
		: process.env.PORT
		? parseInt(process.env.PORT)
		: 5000

if (process.env.SKIP_FLASK !== 'true') {
	// Start Flask application
	log('Starting Flask API server...')

	// First, seed the database
	const seed = spawn('python', ['seed_db.py'], {
		env: process.env,
		stdio: 'pipe',
	})

	seed.stdout?.on('data', data => {
		log(data.toString().trim(), 'seed')
	})

	seed.stderr?.on('data', data => {
		console.error(`Seed error: ${data}`)
	})

	seed.on('close', code => {
		if (code === 0) {
			log('Database seeded successfully', 'seed')
		} else {
			log(`Database seed failed with code ${code}`, 'seed')
		}

		// Start Flask server on port 5001
		const flaskEnv = { ...process.env, PORT: FLASK_PORT.toString() }
		const flask = spawn('python', ['app.py'], {
			env: flaskEnv,
			stdio: 'pipe',
		})

		flask.stdout?.on('data', data => {
			log(data.toString().trim(), 'flask')
		})

		flask.stderr?.on('data', data => {
			console.error(`Flask: ${data}`)
		})

		flask.on('error', error => {
			console.error(`Failed to start Flask: ${error.message}`)
			process.exit(1)
		})

		flask.on('exit', code => {
			log(`Flask process exited with code ${code}`, 'flask')
			process.exit(code || 0)
		})

		// Handle termination signals
		process.on('SIGTERM', () => {
			flask.kill('SIGTERM')
		})

		process.on('SIGINT', () => {
			flask.kill('SIGINT')
		})
	})
} else {
	log('Skipping Flask API server (standalone mode)')
}

// Proxy API requests to Flask
app.use(
	'/api',
	createProxyMiddleware({
		target: `http://localhost:${FLASK_PORT}`,
		changeOrigin: true,
		pathRewrite: {
			'^/api': '/api', // Keep /api prefix when forwarding to Flask
		},
	})
)

// Setup Vite or Static Server
const server = app.listen(SERVER_PORT, '0.0.0.0', async () => {
	if (process.env.NODE_ENV === 'development') {
		await setupVite(app, server)
	} else {
		// In production, we assume Nginx might be serving static files,
		// but we still provide a fallback through Express just in case.
		const { serveStatic } = await import('./vite')
		serveStatic(app)
	}
	log(`Server running on http://0.0.0.0:${SERVER_PORT}`)
})

// WebSocket Server
import { chat_messages } from '@shared/schema'
import { WebSocket, WebSocketServer } from 'ws'
import { db } from './db'

const wss = new WebSocketServer({ server, path: '/ws' })

// Track connected clients
const clients = new Map<string, WebSocket>()
const adminClients = new Set<WebSocket>()

wss.on('connection', (ws, req) => {
	const url = new URL(req.url || '', `http://${req.headers.host}`)
	const userId = url.searchParams.get('userId')
	const isAdmin = url.searchParams.get('isAdmin') === 'true'

	if (!userId) {
		ws.close()
		return
	}

	// Register client
	clients.set(userId, ws)
	if (isAdmin) {
		adminClients.add(ws)
		log(`Admin connected: ${userId}`, 'ws')
	} else {
		log(`User connected: ${userId}`, 'ws')
	}

	ws.on('message', async message => {
		try {
			const data = JSON.parse(message.toString())

			// Expected format: { type: 'message', content: '...', recipientId: '...' (optional if to admin) }
			if (data.type === 'message') {
				const { content, recipientId } = data

				// Determine recipient (Admin sends to User, User sends to Admin)
				// IfisAdmin, send to recipientId. If User, send to all admins.

				let targetId = recipientId

				/* 
          Logic:
          - User -> Admin: 
            - Store in DB: user_id=sender(userId), sender_id=userId, content=content
            - Broadcast to ALL connected admins
            - Echo back to sender for confirmation
          - Admin -> User:
            - Store in DB: user_id=recipientId, sender_id=admin(userId), content=content
            - Send to specific connected user
            - Echo back to sender (admin)
        */

				const isMessageFromAdmin = isAdmin

				// The "user_id" column in DB always represents the CUSTOMER in the conversation context
				// The "sender_id" is who actually wrote the message

				const dbUserId = isMessageFromAdmin ? recipientId : userId

				if (!dbUserId) {
					console.error('Missing target user ID for message')
					return
				}

				// 1. Save to DB
				const [savedMsg] = await db
					.insert(chat_messages)
					.values({
						user_id: dbUserId,
						sender_id: userId,
						content: content,
						is_read: false,
					})
					.returning()

				// 2. Broadcast
				const payload = JSON.stringify({
					type: 'new_message',
					message: savedMsg,
				})

				// Send to self (confirmation)
				ws.send(payload)

				if (isMessageFromAdmin) {
					// Send to specific user
					const clientWs = clients.get(recipientId)
					if (clientWs && clientWs.readyState === WebSocket.OPEN) {
						clientWs.send(payload)
					}
				} else {
					// Send to all admins
					adminClients.forEach(adminWs => {
						if (adminWs.readyState === WebSocket.OPEN) {
							adminWs.send(payload)
						}
					})
				}
			} else if (data.type === 'typing') {
				// Handle typing indicators if needed later
			}
		} catch (e) {
			console.error('WebSocket message error:', e)
		}
	})

	ws.on('close', () => {
		clients.delete(userId)
		if (isAdmin) {
			adminClients.delete(ws)
		}
	})
})
