import os
import hashlib
import sqlite3
from flask import Flask, Response
from ics import Calendar, Event
from datetime import datetime

SECRET_KEY = "your_secret_key_here"

app = Flask(__name__)

# Helper function: Generate a random filename
def generate_filename(category_name):
    random_string = os.urandom(16).hex()
    hash_object = hashlib.sha256((random_string + SECRET_KEY + category_name).encode())
    return hash_object.hexdigest()

# Helper function: Fetch data from SQLite
def fetch_from_db(db_name, table_name):
    """
    Fetch all rows from a specified table in a SQLite database.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Helper function: Fetch notice for a specific event
def fetch_notice_for_event(event_name, db_name="notices.db"):
    """
    Fetch a notice for a specific event from the notices database.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT notice FROM notices WHERE event_name = ?", (event_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

@app.route("/api/calendar/machines.ics", methods=["GET"])
def generate_machines_calendar():
    """
    Generate a calendar for all HTB Machines from the database.
    Includes Notices if available and excludes past events.
    """
    calendar = Calendar()
    machines = fetch_from_db("machines.db", "tracked_machines")
    current_date = datetime.now()

    # Add events for each machine
    for machine in machines:
        release_date = datetime.fromisoformat(machine[4])  # machine[4] -> release_date
        if release_date < current_date:
            continue  # Skip past events

        event = Event()
        event.name = f"Machine: {machine[1]}"  # machine[1] -> name
        event.begin = release_date.isoformat()
        event.description = f"Difficulty: {machine[3]}, OS: {machine[2]}"  # machine[3] -> difficulty, machine[2] -> OS

        # Fetch and append notice if available
        notice = fetch_notice_for_event(machine[1])
        if notice:
            event.description += f"\nNotice: {notice}"

        calendar.events.add(event)

    # Generate a filename and save the calendar
    filename = generate_filename("machines")
    with open(f"{filename}.ics", "w") as file:
        file.writelines(str(calendar))

    return Response(str(calendar), mimetype="text/calendar")

@app.route("/api/calendar/challenges.ics", methods=["GET"])
def generate_challenges_calendar():
    """
    Generate a calendar for all HTB Challenges from the database.
    Includes Notices if available and excludes past events.
    """
    calendar = Calendar()
    challenges = fetch_from_db("challenges.db", "tracked_challenges")
    current_date = datetime.now()

    # Add events for each challenge
    for challenge in challenges:
        release_date = datetime.fromisoformat(challenge[4])  # challenge[4] -> release_date
        if release_date < current_date:
            continue  # Skip past events

        event = Event()
        event.name = f"Challenge: {challenge[1]}"  # challenge[1] -> name
        event.begin = release_date.isoformat()
        event.description = f"Difficulty: {challenge[2]}, Category: {challenge[3]}"  # challenge[2] -> difficulty, challenge[3] -> category

        # Fetch and append notice if available
        notice = fetch_notice_for_event(challenge[1])
        if notice:
            event.description += f"\nNotice: {notice}"

        calendar.events.add(event)

    # Generate a filename and save the calendar
    filename = generate_filename("challenges")
    with open(f"{filename}.ics", "w") as file:
        file.writelines(str(calendar))

    return Response(str(calendar), mimetype="text/calendar")

# Run the app (for local testing)
if __name__ == "__main__":
    app.run(debug=True, port=5000)
