import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.database import get_db_connection

def verify():
    print("Verifying App Initialization...")
    try:
        app = create_app()
        print("✅ App created successfully.")
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return

    print("\nVerifying Database Connection & Admin User...")
    try:
        with app.app_context():
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = TRUE")
            count = cur.fetchone()['count']
            print(f"✅ Database connected. Admin count: {count}")
            
            if count > 0:
                cur.execute("SELECT email FROM users WHERE is_admin = TRUE LIMIT 1")
                print(f"ℹ️ Found admin: {cur.fetchone()['email']}")
            else:
                print("⚠️ No admin user found. Setup required.")
                
            cur.close()
            conn.close()
    except Exception as e:
        print(f"❌ Database check failed: {e}")

if __name__ == "__main__":
    verify()
