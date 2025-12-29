import os
import sys
from dotenv import load_dotenv
import psycopg2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = cur.fetchall()
    print("📋 Tables in DB:")
    for table in tables:
        print(f"- {table[0]}")
        
        # If orders exists, show columns
        if table[0] == 'orders':
            print("   Columns:")
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders'")
            cols = cur.fetchall()
            for col in cols:
                print(f"   - {col[0]} ({col[1]})")

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
