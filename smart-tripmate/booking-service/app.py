import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = Path(__file__).resolve().parent / "booking.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_city TEXT NOT NULL,
            to_city TEXT NOT NULL,
            price REAL NOT NULL,
            duration INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_city TEXT NOT NULL,
            to_city TEXT NOT NULL,
            price REAL NOT NULL,
            duration INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            type TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL
        );
        """
    )

    has_data = conn.execute("SELECT COUNT(*) AS c FROM flights").fetchone()["c"]
    if has_data == 0:
        conn.executescript(
            """
            INSERT INTO flights (from_city, to_city, price, duration) VALUES
            ('Delhi', 'Mumbai', 4500, 130),
            ('Delhi', 'Bengaluru', 6200, 170),
            ('Mumbai', 'Goa', 2800, 75),
            ('Chennai', 'Kolkata', 5400, 150);

            INSERT INTO trains (from_city, to_city, price, duration) VALUES
            ('Delhi', 'Mumbai', 1800, 900),
            ('Delhi', 'Bengaluru', 2200, 1800),
            ('Mumbai', 'Goa', 900, 600),
            ('Chennai', 'Kolkata', 2100, 1650);

            INSERT INTO hotels (city, price_per_night, type) VALUES
            ('Mumbai', 1500, 'budget'),
            ('Mumbai', 3500, 'standard'),
            ('Mumbai', 7000, 'luxury'),
            ('Bengaluru', 1200, 'budget'),
            ('Bengaluru', 3000, 'standard'),
            ('Goa', 1000, 'budget'),
            ('Goa', 2800, 'standard'),
            ('Goa', 6000, 'luxury');

            INSERT INTO activities (city, name, price) VALUES
            ('Mumbai', 'City Tour', 900),
            ('Mumbai', 'Museum Pass', 500),
            ('Bengaluru', 'Food Walk', 700),
            ('Goa', 'Beach Cruise', 1400),
            ('Goa', 'Water Sports', 2200);
            """
        )

    conn.commit()
    conn.close()


def fetch_rows(query, params=()):
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "booking-service"})


@app.get("/flights")
def flights():
    from_city = request.args.get("from_city")
    to_city = request.args.get("to_city")
    query = "SELECT from_city, to_city, price, duration FROM flights WHERE 1=1"
    params = []
    if from_city:
        query += " AND from_city = ?"
        params.append(from_city)
    if to_city:
        query += " AND to_city = ?"
        params.append(to_city)
    return jsonify({"flights": fetch_rows(query, tuple(params))})


@app.get("/trains")
def trains():
    from_city = request.args.get("from_city")
    to_city = request.args.get("to_city")
    query = "SELECT from_city, to_city, price, duration FROM trains WHERE 1=1"
    params = []
    if from_city:
        query += " AND from_city = ?"
        params.append(from_city)
    if to_city:
        query += " AND to_city = ?"
        params.append(to_city)
    return jsonify({"trains": fetch_rows(query, tuple(params))})


@app.get("/hotels")
def hotels():
    city = request.args.get("city")
    hotel_type = request.args.get("type")
    query = "SELECT city, price_per_night, type FROM hotels WHERE 1=1"
    params = []
    if city:
        query += " AND city = ?"
        params.append(city)
    if hotel_type:
        query += " AND type = ?"
        params.append(hotel_type)
    return jsonify({"hotels": fetch_rows(query, tuple(params))})


@app.get("/activities")
def activities():
    city = request.args.get("city")
    query = "SELECT city, name, price FROM activities"
    params = ()
    if city:
        query += " WHERE city = ?"
        params = (city,)
    return jsonify({"activities": fetch_rows(query, params)})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5005)
