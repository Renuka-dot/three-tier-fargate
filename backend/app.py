from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "appdb")


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=5
    )


def initialize_database():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                )
            """)
        connection.commit()
    finally:
        connection.close()


@app.route("/api/health")
def health():
    return jsonify({
        "status": "UP"
    })


@app.route("/api/users", methods=["GET"])
def get_users():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name FROM users ORDER BY id DESC"
            )

            rows = cursor.fetchall()

            users = [
                {
                    "id": row[0],
                    "name": row[1]
                }
                for row in rows
            ]

            return jsonify(users)

    finally:
        connection.close()


@app.route("/api/users", methods=["POST"])
def add_user():

    data = request.get_json()

    name = data.get("name", "").strip()

    if not name:
        return jsonify({
            "error": "Name is required"
        }), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users(name) VALUES(%s)",
                (name,)
            )

        connection.commit()

        return jsonify({
            "message": "User added successfully"
        }), 201

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()

    app.run(
        host="0.0.0.0",
        port=5000
    )
