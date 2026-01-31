"""
Complete Database Viewer
View all records in your church database
"""

from app import app, db, Admin, Event, Inquiry, SpaceRental
from datetime import datetime

def view_admins():
    """View all admin users"""
    print("\n" + "=" * 80)
    print("👤 ADMIN USERS")
    print("=" * 80)
    
    admins = Admin.query.all()
    
    if not admins:
        print("❌ No admin users found")
        return
    
    print(f"Found {len(admins)} admin(s):\n")
    
    for admin in admins:
        print(f"ID: {admin.id}")
        print(f"Username: {admin.username}")
        print(f"Password Hash: {admin.password_hash[:50]}...")
        print(f"Created: {admin.created_at}")
        print("-" * 80)

def view_events():
    """View all events"""
    print("\n" + "=" * 80)
    print("📅 EVENTS")
    print("=" * 80)
    
    events = Event.query.order_by(Event.event_date.desc()).all()
    
    if not events:
        print("❌ No events found")
        return
    
    print(f"Found {len(events)} event(s):\n")
    
    for event in events:
        print(f"ID: {event.id}")
        print(f"Title: {event.title}")
        print(f"Date: {event.event_date}")
        print(f"Description: {event.description}")
        print(f"Image Path: {event.image_path or 'None'}")
        print(f"Created: {event.created_at}")
        print("-" * 80)

def view_inquiries():
    """View all inquiries"""
    print("\n" + "=" * 80)
    print("📧 INQUIRIES")
    print("=" * 80)
    
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    
    if not inquiries:
        print("❌ No inquiries found")
        return
    
    print(f"Found {len(inquiries)} inquir(y/ies):\n")
    
    for inquiry in inquiries:
        print(f"ID: {inquiry.id}")
        print(f"Name: {inquiry.name}")
        print(f"Phone: {inquiry.phone}")
        print(f"Email: {inquiry.email}")
        print(f"Note: {inquiry.note}")
        print(f"Created: {inquiry.created_at}")
        print("-" * 80)

def view_space_rentals():
    """View all space rentals"""
    print("\n" + "=" * 80)
    print("🏛️ SPACE RENTALS")
    print("=" * 80)
    
    rentals = SpaceRental.query.order_by(SpaceRental.created_at.desc()).all()
    
    if not rentals:
        print("❌ No space rentals found")
        return
    
    print(f"Found {len(rentals)} rental(s):\n")
    
    for rental in rentals:
        print(f"ID: {rental.id}")
        print(f"Name: {rental.name}")
        print(f"Phone: {rental.phone}")
        print(f"Email: {rental.email}")
        print(f"Event Type: {rental.event_type}")
        print(f"Space: {rental.space_requested}")
        print(f"Date: {rental.event_date}")
        print(f"Time: {rental.start_time} - {rental.end_time}")
        print(f"Guests: {rental.guest_count}")
        print(f"Additional Needs: {rental.additional_needs or 'None'}")
        print(f"Message: {rental.message or 'None'}")
        print(f"Created: {rental.created_at}")
        print("-" * 80)

def view_database_info():
    """View database file information"""
    import os
    print("\n" + "=" * 80)
    print("💾 DATABASE FILE INFO")
    print("=" * 80)
    
    if os.path.exists('instance/church.db'):
        size = os.path.getsize('church.db')
        size_mb = size / (1024 * 1024)
        modified = datetime.fromtimestamp(os.path.getmtime('church.db'))
        
        print(f"✅ Database exists: church.db")
        print(f"Size: {size:,} bytes ({size_mb:.2f} MB)")
        print(f"Last Modified: {modified}")
    else:
        print("❌ Database file not found: church.db")
        print("Run: python complete_fix.py")

def get_table_counts():
    """Get count of records in each table"""
    print("\n" + "=" * 80)
    print("📊 RECORD COUNTS")
    print("=" * 80)
    
    try:
        admin_count = Admin.query.count()
        event_count = Event.query.count()
        inquiry_count = Inquiry.query.count()
        rental_count = SpaceRental.query.count()
        
        print(f"Admins:        {admin_count}")
        print(f"Events:        {event_count}")
        print(f"Inquiries:     {inquiry_count}")
        print(f"Space Rentals: {rental_count}")
        print(f"Total Records: {admin_count + event_count + inquiry_count + rental_count}")
        
    except Exception as e:
        print(f"❌ Error counting records: {e}")

def search_event(event_id):
    """Search for a specific event"""
    print("\n" + "=" * 80)
    print(f"🔍 SEARCHING FOR EVENT ID: {event_id}")
    print("=" * 80)
    
    try:
        event = Event.query.get(event_id)
        
        if event:
            print("✅ Event Found!\n")
            print(f"ID: {event.id}")
            print(f"Title: {event.title}")
            print(f"Date: {event.event_date}")
            print(f"Description: {event.description}")
            print(f"Image Path: {event.image_path or 'None'}")
            print(f"Created: {event.created_at}")
        else:
            print(f"❌ Event with ID {event_id} not found")
            print("\n📋 Available Event IDs:")
            all_events = Event.query.all()
            for e in all_events:
                print(f"   - ID {e.id}: {e.title}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def export_to_csv():
    """Export database records to CSV files"""
    import csv
    
    print("\n" + "=" * 80)
    print("📤 EXPORTING TO CSV")
    print("=" * 80)
    
    try:
        # Export Events
        events = Event.query.all()
        if events:
            with open('events_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Title', 'Date', 'Description', 'Image Path', 'Created'])
                for event in events:
                    writer.writerow([
                        event.id,
                        event.title,
                        event.event_date,
                        event.description,
                        event.image_path or '',
                        event.created_at
                    ])
            print(f"✅ Exported {len(events)} events to events_export.csv")
        
        # Export Inquiries
        inquiries = Inquiry.query.all()
        if inquiries:
            with open('inquiries_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Phone', 'Email', 'Note', 'Created'])
                for inquiry in inquiries:
                    writer.writerow([
                        inquiry.id,
                        inquiry.name,
                        inquiry.phone,
                        inquiry.email,
                        inquiry.note,
                        inquiry.created_at
                    ])
            print(f"✅ Exported {len(inquiries)} inquiries to inquiries_export.csv")
        
        # Export Space Rentals
        rentals = SpaceRental.query.all()
        if rentals:
            with open('rentals_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Phone', 'Email', 'Event Type', 'Space', 'Date', 'Time', 'Guests', 'Created'])
                for rental in rentals:
                    writer.writerow([
                        rental.id,
                        rental.name,
                        rental.phone,
                        rental.email,
                        rental.event_type,
                        rental.space_requested,
                        rental.event_date,
                        f"{rental.start_time} - {rental.end_time}",
                        rental.guest_count,
                        rental.created_at
                    ])
            print(f"✅ Exported {len(rentals)} rentals to rentals_export.csv")
        
        print("\n✅ Export complete!")
        
    except Exception as e:
        print(f"❌ Export error: {e}")

def main_menu():
    """Interactive menu"""
    with app.app_context():
        while True:
            print("\n" + "=" * 80)
            print("🗄️  CHURCH DATABASE VIEWER")
            print("=" * 80)
            print("\n1. View All Records")
            print("2. View Admins")
            print("3. View Events")
            print("4. View Inquiries")
            print("5. View Space Rentals")
            print("6. Search Event by ID")
            print("7. Show Record Counts")
            print("8. Database File Info")
            print("9. Export to CSV")
            print("0. Exit")
            
            choice = input("\nEnter your choice (0-9): ").strip()
            
            if choice == '1':
                view_database_info()
                get_table_counts()
                view_admins()
                view_events()
                view_inquiries()
                view_space_rentals()
                
            elif choice == '2':
                view_admins()
                
            elif choice == '3':
                view_events()
                
            elif choice == '4':
                view_inquiries()
                
            elif choice == '5':
                view_space_rentals()
                
            elif choice == '6':
                event_id = input("Enter Event ID: ").strip()
                if event_id.isdigit():
                    search_event(int(event_id))
                else:
                    print("❌ Invalid ID")
                    
            elif choice == '7':
                get_table_counts()
                
            elif choice == '8':
                view_database_info()
                
            elif choice == '9':
                export_to_csv()
                
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice")
            
            input("\nPress Enter to continue...")

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()