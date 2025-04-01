from flask import Flask, jsonify
import requests
import sqlite3
import time


app = Flask(__name__)

JOKES_API_URL="https://v2.jokeapi.dev/joke/Any?amount=100"
# "https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Dark,Pun,Spooky,Christmas?blacklistFlags=nsfw,political,sexist&amount=100"


# SQLite Database File
DB_NAME = "jokes.db"

def create_table():
    """Creates a jokes table if it does not exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            type TEXT,
            joke TEXT,
            setup TEXT,
            delivery TEXT,
            nsfw INTEGER,
            political INTEGER,
            sexist INTEGER,
            safe INTEGER,
            lang TEXT
        );
    """)
    conn.commit()
    conn.close()

def fetch_jokes(min_jokes=100):
    """Fetches jokes from the external JokeAPI."""
    jokes = []
    
    while len(jokes) < min_jokes:
        response = requests.get(JOKES_API_URL)
        if response.status_code != 200:
            return {"error": "Failed to fetch jokes from API"}

        try:
            new_jokes = response.json().get("jokes", [])
        except requests.exceptions.JSONDecodeError:
            return {"error": "Invalid JSON response from API"}

        processed_jokes = []

        for joke in new_jokes:
            processed_jokes.append((
                joke.get("category", ""),
                joke.get("type", ""),
                joke.get("joke", "") if joke["type"] == "single" else None,
                joke.get("setup", "") if joke["type"] == "twopart" else None,
                joke.get("delivery", "") if joke["type"] == "twopart" else None,
                int(joke["flags"]["nsfw"]),
                int(joke["flags"]["political"]),
                int(joke["flags"]["sexist"]),
                int(joke["safe"]),
                joke.get("lang", "en")
            ))

        # store_jokes(processed_jokes)
        jokes.extend(processed_jokes)
        print(f"Fetched {len(jokes)} jokes so far...")  # Progress update

        time.sleep(1)  # Delay to prevent hitting rate limits

    store_jokes(jokes[:min_jokes])  # Store exactly 100 jokes
    return {"message": f"{len(jokes[:min_jokes])} jokes stored successfully"}


@app.route("/fetch", methods=["GET"])
def fetch_and_store_jokes():
    """API Endpoint to fetch and store jokes."""
    result = fetch_jokes()
    return jsonify(result)


def store_jokes(jokes):
    """Stores jokes in the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT INTO jokes (category, type, joke, setup, delivery, nsfw, political, sexist, safe, lang)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, jokes)

    conn.commit()
    conn.close()


@app.route("/jokes", methods=["GET"])
def get_jokes():
    """API Endpoint to get stored jokes."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jokes")
    jokes = cursor.fetchall()
    conn.close()

    return jsonify({"jokes": jokes})


if __name__ == "__main__":
    create_table()
    app.run(debug=True,port=5001)