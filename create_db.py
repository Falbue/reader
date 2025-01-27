from scripts import *

connect = sqlite3.connect(DB_PATH)
cursor = connect.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER,
    username TEXT,
    message INTEGER,
    time_registration DATE,
    read JSON DEFAULT '{}',
    config JSON DEFAULT '{}'
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_file TEXT,
    name TEXT,
    time_add DATE,
    user_id INTEGER
)''')

connect.commit()
connect.close()
print("База данных создана")