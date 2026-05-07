#!/usr/bin/env python
"""Check what's actually in the Neon database."""
import os
from dotenv import load_dotenv
import psycopg2

# Load .env
load_dotenv()
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("❌ DATABASE_URL not found in .env")
    exit(1)

print(f"🔌 Connecting to Neon: {db_url.split('@')[1][:30]}...")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Check if tables exist
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print(f"\n📋 Tables in public schema: {[t[0] for t in tables]}")
    
    # Check row counts
    for table in ['outlets', 'food_items', 'sales']:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"   {table}: {count} rows")
    
    # Sample data
    print("\n📊 Sample outlets:")
    cur.execute("SELECT id, name, location FROM outlets LIMIT 3;")
    for row in cur.fetchall():
        print(f"   {row}")
    
    print("\n📊 Sample food_items:")
    cur.execute("SELECT id, name, category FROM food_items LIMIT 3;")
    for row in cur.fetchall():
        print(f"   {row}")
    
    print("\n📊 Sample sales:")
    cur.execute("SELECT outlet_id, food_item_id, date, quantity_sold FROM sales LIMIT 3;")
    for row in cur.fetchall():
        print(f"   {row}")
    
    conn.close()
    print("\n✅ Query complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
