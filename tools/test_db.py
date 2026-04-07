import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_BASE_DIR, 'workorch', '.env')
load_dotenv(_ENV_PATH)

def test_connection():
    print("Testing connection to AlloyDB via Proxy...")
    try:
        conn = psycopg2.connect(
            host=os.environ.get("ALLOYDB_HOST"),
            user=os.environ.get("ALLOYDB_USER"),
            password=os.environ.get("ALLOYDB_PASSWORD"),
            dbname=os.environ.get("ALLOYDB_DB_NAME")
        )
        print("✅ Connection successful!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()
        print(f"Total tables found: {len(tables)}")
        for table in tables:
            print(f" - {table[0]}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure the AlloyDB Auth Proxy is running and listening on 127.0.0.1:5432")

if __name__ == "__main__":
    test_connection()
