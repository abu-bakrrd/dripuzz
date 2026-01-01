import sys
import os
import psycopg2
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add path to root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_bot.ai_db_helper import get_db_connection

def inspect_schema():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"📊 Database Schema Report")
        print(f"========================")

        for table in tables:
            table_name = table['table_name']
            print(f"\n📁 Table: {table_name}")
            print(f"------------------------")
            
            # Get columns for this table
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cur.fetchall()
            
            for col in columns:
                c_name = col['column_name']
                c_type = col['data_type']
                c_null = col['is_nullable']
                print(f"  - {c_name:<20} {c_type:<15} (Null: {c_null})")

            # Get row count
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
            count = cur.fetchone()
            print(f"  Rows: {count['cnt']}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error inspecting schema: {e}")

if __name__ == "__main__":
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all columns for 'products' specifically to be sure
        print("🔍 Detailed 'products' table columns:")
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'products'")
        for row in cur.fetchall():
            print(f"  - {row['column_name']}: {row['data_type']}")
            
        # Check if there are products with quantity 0
        cur.execute("SELECT COUNT(*) FROM product_inventory WHERE quantity = 0")
        zero_qty = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM product_inventory WHERE quantity > 0")
        pos_qty = cur.fetchone()[0]
        print(f"\n📦 Inventory Stats:")
        print(f"  - Records with quantity > 0: {pos_qty}")
        print(f"  - Records with quantity = 0: {zero_qty}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

