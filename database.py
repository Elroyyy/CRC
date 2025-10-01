import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash


def create_database():
    """Create the church database and all tables"""

    # Connect to SQLite database (creates file if doesn't exist)
    conn = sqlite3.connect('church.db')
    cursor = conn.cursor()

    print("Creating database tables...")

    # Create Admin table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS admin
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       username
                       VARCHAR
                   (
                       80
                   ) UNIQUE NOT NULL,
                       password_hash VARCHAR
                   (
                       200
                   ) NOT NULL,
                       created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                       )
                   ''')

    # Create Event table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS event
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       VARCHAR
                   (
                       200
                   ) NOT NULL,
                       description TEXT NOT NULL,
                       event_date DATE NOT NULL,
                       image_path VARCHAR
                   (
                       500
                   ),
                       created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                       )
                   ''')

    # Create Inquiry table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS inquiry
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       VARCHAR
                   (
                       100
                   ) NOT NULL,
                       phone VARCHAR
                   (
                       20
                   ) NOT NULL,
                       email VARCHAR
                   (
                       100
                   ) NOT NULL,
                       note TEXT NOT NULL,
                       created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                       )
                   ''')

    # Create Space Rental table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS space_rental
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       VARCHAR
                   (
                       100
                   ) NOT NULL,
                       phone VARCHAR
                   (
                       20
                   ) NOT NULL,
                       email VARCHAR
                   (
                       100
                   ) NOT NULL,
                       event_type VARCHAR
                   (
                       100
                   ) NOT NULL,
                       space_requested VARCHAR
                   (
                       100
                   ) NOT NULL,
                       event_date DATE NOT NULL,
                       start_time VARCHAR
                   (
                       20
                   ) NOT NULL,
                       end_time VARCHAR
                   (
                       20
                   ) NOT NULL,
                       guest_count INTEGER NOT NULL,
                       additional_needs TEXT,
                       message TEXT,
                       created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                       )
                   ''')

    # Check if admin exists, if not create default admin
    cursor.execute('SELECT COUNT(*) FROM admin')
    admin_count = cursor.fetchone()[0]

    if admin_count == 0:
        print("Creating default admin user...")
        password_hash = generate_password_hash('admin123')
        cursor.execute('''
                       INSERT INTO admin (username, password_hash, created_at)
                       VALUES (?, ?, ?)
                       ''', ('admin', password_hash, datetime.now()))

    # Insert sample events if table is empty
    cursor.execute('SELECT COUNT(*) FROM event')
    event_count = cursor.fetchone()[0]

    if event_count == 0:
        print("Adding sample events...")
        sample_events = [
            ('Easter Celebration Service',
             'A joyous celebration of Christ\'s resurrection with special music, testimonies, and communion.',
             '2024-03-31', None),
            ('Community Outreach Program', 'Serving our local community with food distribution and prayer ministry.',
             '2024-03-15', None),
            ('Youth Revival Conference',
             'A powerful weekend of worship, teaching, and fellowship for our young people.', '2024-02-28', None),
            ('Christmas Celebration',
             'A beautiful Christmas service celebrating the birth of our Savior with carols and candlelight.',
             '2024-12-25', None),
            ('Baptism Sunday', 'A sacred time of baptisms as new believers publicly declare their faith.', '2024-11-12',
             None)
        ]

        for title, description, event_date, image_path in sample_events:
            cursor.execute('''
                           INSERT INTO event (title, description, event_date, image_path, created_at)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (title, description, event_date, image_path, datetime.now()))

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Database setup completed successfully!")
    print("Default admin credentials:")
    print("Username: admin")
    print("Password: admin123")


def check_database():
    """Check database contents"""
    conn = sqlite3.connect('church.db')
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables in database: {[table[0] for table in tables]}")

    # Check admin count
    cursor.execute('SELECT COUNT(*) FROM admin')
    admin_count = cursor.fetchone()[0]
    print(f"Admin users: {admin_count}")

    # Check event count
    cursor.execute('SELECT COUNT(*) FROM event')
    event_count = cursor.fetchone()[0]
    print(f"Eefvents: {event_count}")

    # Check inquiry count
    cursor.execute('SELECT COUNT(*) FROM inquiry')
    inquiry_count = cursor.fetchone()[0]
    print(f"Inquiries: {inquiry_count}")

    # Check space rental count
    cursor.execute('SELECT COUNT(*) FROM space_rental')
    rental_count = cursor.fetchone()[0]
    print(f"Space rentals: {rental_count}")

    conn.close()


if __name__ == '__main__':
    create_database()
    check_database()