import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect("../church.db")  # change to your .db file name
cursor = conn.cursor()

# Choose the table you want to view
table_name = "inquiry"   # change to your table name

# Select all rows from the table
cursor.execute(f"SELECT * FROM {table_name}")

rows = cursor.fetchall()

# Print results
print(f"Data from {table_name}:")
for row in rows:
    print(row)

cursor.close()
conn.close()
