import sqlite3

# Kết nối đến database (nếu chưa có sẽ tự tạo)
conn = sqlite3.connect("./instance/database.db")

# Tạo một con trỏ để thao tác với database
cursor = conn.cursor()

cursor.execute("SELECT * FROM User")
rows = cursor.fetchall()  # Lấy tất cả kết quả
for row in rows:
    print(row)
    
conn.close()
