import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        if 'neon.tech' in database_url or 'amazonaws.com' in database_url:
            if 'sslmode=' not in database_url:
                database_url = database_url + ('&' if '?' in database_url else '?') + 'sslmode=require'
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            database=os.getenv('PGDATABASE'),
            cursor_factory=RealDictCursor
        )
    return conn

def migrate():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("Adding updated_at to products...")
        cur.execute('''
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='products' AND column_name='updated_at') THEN
                    ALTER TABLE products ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        ''')

        print("Adding updated_at to categories...")
        cur.execute('''
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='categories' AND column_name='updated_at') THEN
                    ALTER TABLE categories ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        ''')

        print("Creating trigger function...")
        cur.execute('''
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        ''')

        for table in ['products', 'categories', 'platform_settings', 'product_inventory']:
            print(f"Adding trigger to {table}...")
            cur.execute(f'''
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_{table}_updated_at') THEN
                        CREATE TRIGGER update_{table}_updated_at
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                    END IF;
                END $$;
            ''')
        
        conn.commit()
        print("Migration successful!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
