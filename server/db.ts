import { Pool, neonConfig } from '@neondatabase/serverless'
import * as schema from '@shared/schema'
import { drizzle } from 'drizzle-orm/neon-serverless'
import ws from 'ws'

neonConfig.webSocketConstructor = ws

if (!process.env.DATABASE_URL) {
	throw new Error(
		'DATABASE_URL must be set. Did you forget to provision a database?'
	)
}

export const pool = new Pool({
	connectionString: process.env.DATABASE_URL,
	ssl: process.env.DATABASE_URL?.includes('localhost') ? false : undefined,
})
export const db = drizzle({ client: pool, schema })
