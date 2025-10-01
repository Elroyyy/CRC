"""
Quick fix for database sync issues between raw SQL and SQLAlchemy
Run this script to fix the admin login issue
"""

import os
from datetime import datetime
from app import app, db, Admin, Event, SpaceRental, Inquiry
from werkzeug.security import generate_password_hash


def fix_database():
    """Fix database by recreating with SQLAlchemy"""

    print("🔧 Fixing database synchronization...")

    with app.app_context():
        try:
            # Drop all existing tables to start fresh
            db.drop_all()
            print("✅ Dropped existing tables")

            # Create all tables using SQLAlchemy models
            db.create_all()
            print("✅ Created tables using SQLAlchemy models")

            # Create default admin user
            if not Admin.query.first():
                admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin)
                print("✅ Created default admin user")

            # Add sample events
            if not Event.query.first():
                sample_events = [
                    Event(
                        title='Easter Celebration Service',
                        description='A joyous celebration of Christ\'s resurrection with special music, testimonies, and communion.',
                        event_date=datetime.strptime('2024-03-31', '%Y-%m-%d').date(),
                        image_path=None
                    ),
                    Event(
                        title='Community Outreach Program',
                        description='Serving our local community with food distribution and prayer ministry.',
                        event_date=datetime.strptime('2024-03-15', '%Y-%m-%d').date(),
                        image_path=None
                    ),
                    Event(
                        title='Youth Revival Conference',
                        description='A powerful weekend of worship, teaching, and fellowship for our young people.',
                        event_date=datetime.strptime('2024-02-28', '%Y-%m-%d').date(),
                        image_path=None
                    ),
                    Event(
                        title='Christmas Celebration',
                        description='A beautiful Christmas service celebrating the birth of our Savior with carols and candlelight.',
                        event_date=datetime.strptime('2024-12-25', '%Y-%m-%d').date(),
                        image_path=None
                    ),
                    Event(
                        title='Baptism Sunday',
                        description='A sacred time of baptisms as new believers publicly declare their faith.',
                        event_date=datetime.strptime('2024-11-12', '%Y-%m-%d').date(),
                        image_path=None
                    )
                ]

                for event in sample_events:
                    db.session.add(event)

                print("✅ Added sample events")

            # Commit all changes
            db.session.commit()
            print("✅ All changes committed to database")

            # Verify the fix worked
            admin_count = Admin.query.count()
            event_count = Event.query.count()

            print(f"\n📊 Database Status:")
            print(f"   Admins: {admin_count}")
            print(f"   Events: {event_count}")
            print(f"   Inquiries: {Inquiry.query.count()}")
            print(f"   Space Rentals: {SpaceRental.query.count()}")

            if admin_count > 0:
                print(f"\n🎉 Database fixed successfully!")
                print(f"Admin credentials:")
                print(f"   Username: admin")
                print(f"   Password: admin123")
            else:
                print(f"\n❌ Something went wrong - no admin users found")

        except Exception as e:
            print(f"❌ Error fixing database: {e}")
            db.session.rollback()


def test_login():
    """Test if admin login works now"""
    print(f"\n🧪 Testing admin login...")

    with app.app_context():
        try:
            admin = Admin.query.filter_by(username='admin').first()
            if admin:
                print(f"✅ Admin user found: {admin.username}")
                print(f"✅ Login should work now!")
            else:
                print(f"❌ Admin user not found")
        except Exception as e:
            print(f"❌ Error testing login: {e}")


if __name__ == '__main__':
    print("🚀 Church Website Database Fix")
    print("=" * 40)

    # Check if database file exists
    if os.path.exists('templates/church.db'):
        print("📁 Found existing church.db")
        response = input("Do you want to recreate the database? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            exit()

    fix_database()
    test_login()

    print(f"\n✨ Fix completed! Try running your Flask app now:")
    print(f"   python app.py")