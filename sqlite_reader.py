import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# Show all tables
#cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#tables = cursor.fetchall()
#print("Tables:", tables)

# Example: show data from a specific table
cursor.execute("SELECT * FROM auth_user")  # Adjust table name as needed
rows = cursor.fetchall()
for row in rows:
    print(">>", row)
