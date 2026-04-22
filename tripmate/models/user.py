import sqlite3

class User:
    def __init__(self, id, name, email, hashed_password):
        self.id = id
        self.name = name
        self.email = email
        self.hashed_password = hashed_password
    
    @staticmethod
    def get_by_email(email, conn):
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user:
            return User(user['id'], user['name'], user['email'], user['hashed_password'])
        return None
    
    @staticmethod
    def create(name, email, hashed_password, conn):
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)',
                      (name, email, hashed_password))
        conn.commit()
        return cursor.lastrowid
