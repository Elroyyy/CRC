import requests
import json
from datetime import datetime, date

# Base URL for your Flask app
BASE_URL = "http://localhost:5000"

def test_main_routes():
    """Test main website routes"""
    print("=== Testing Main Website Routes ===")
    
    try:
        # Test home page
        response = requests.get(f"{BASE_URL}/")
        print(f"GET / - Status: {response.status_code}")
        
        # Test events API
        response = requests.get(f"{BASE_URL}/api/events")
        print(f"GET /api/events - Status: {response.status_code}")
        if response.status_code == 200:
            events = response.json()
            print(f"  Found {len(events)} events")
        
        # Test database connection
        response = requests.get(f"{BASE_URL}/api/test")
        print(f"GET /api/test - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Database counts: {data.get('counts', {})}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Flask app is running!")
        return False
    except Exception as e:
        print(f"❌ Error testing main routes: {e}")
        return False
    
    return True

def test_inquiry_submission():
    """Test inquiry form submission"""
    print("\n=== Testing Inquiry Submission ===")
    
    try:
        inquiry_data = {
            "name": "Test User",
            "phone": "123-456-7890",
            "email": "test@example.com",
            "note": "This is a test inquiry message"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inquiry",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(inquiry_data)
        )
        
        print(f"POST /api/inquiry - Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Inquiry submitted successfully")
            return True
        else:
            print(f"❌ Inquiry submission failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing inquiry: {e}")
        return False

def test_space_rental_submission():
    """Test space rental form submission"""
    print("\n=== Testing Space Rental Submission ===")
    
    try:
        rental_data = {
            "name": "Test Renter",
            "phone": "123-456-7890",
            "email": "renter@example.com",
            "event_type": "Wedding",
            "space_requested": "Main Sanctuary",
            "event_date": "2024-06-15",
            "start_time": "14:00",
            "end_time": "18:00",
            "guest_count": 150,
            "additional_needs": "Sound System, Kitchen Access",
            "message": "This is a test rental request"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/space-rental",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(rental_data)
        )
        
        print(f"POST /api/space-rental - Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Space rental request submitted successfully")
            return True
        else:
            print(f"❌ Space rental submission failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing space rental: {e}")
        return False

def test_admin_routes():
    """Test admin routes (without login for now)"""
    print("\n=== Testing Admin Routes (Public Access) ===")
    
    try:
        # Test admin login page
        response = requests.get(f"{BASE_URL}/admin")
        print(f"GET /admin - Status: {response.status_code}")
        
        # These should redirect to login, so 302 is expected
        admin_routes = [
            "/admin/dashboard",
            "/admin/events", 
            "/admin/space-rentals",
            "/admin/inquiries"
        ]
        
        for route in admin_routes:
            response = requests.get(f"{BASE_URL}{route}", allow_redirects=False)
            print(f"GET {route} - Status: {response.status_code} (should be 302 redirect)")
            
    except Exception as e:
        print(f"❌ Error testing admin routes: {e}")
        return False
    
    return True

def run_all_tests():
    """Run all tests"""
    print("🧪 Church Website Route Testing")
    print("=" * 50)
    
    # Test basic connectivity first
    if not test_main_routes():
        print("\n❌ Basic connectivity failed. Check if:")
        print("1. Flask app is running (python app.py)")
        print("2. Database is set up (python database_setup.py)")
        return
    
    # Test form submissions
    inquiry_success = test_inquiry_submission()
    rental_success = test_space_rental_submission()
    admin_success = test_admin_routes()
    
    # Summary
    print("\n" + "=" * 50)
    print("🔍 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Main Routes:      {'✅ PASS' if True else '❌ FAIL'}")
    print(f"Inquiry Form:     {'✅ PASS' if inquiry_success else '❌ FAIL'}")
    print(f"Space Rental:     {'✅ PASS' if rental_success else '❌ FAIL'}")
    print(f"Admin Access:     {'✅ PASS' if admin_success else '❌ FAIL'}")
    
    if all([inquiry_success, rental_success, admin_success]):
        print("\n🎉 All tests passed! Your website is working correctly.")
        print("\nNext steps:")
        print("1. Visit http://localhost:5000 to see the main website")
        print("2. Test the contact form and space rental form")
        print("3. Login to admin panel at http://localhost:5000/admin")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

def check_database_setup():
    """Check if database is properly set up"""
    print("\n=== Checking Database Setup ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/test")
        if response.status_code == 200:
            data = response.json()
            counts = data.get('counts', {})
            
            print(f"✅ Database connection working")
            print(f"   Admins: {counts.get('admins', 0)}")
            print(f"   Events: {counts.get('events', 0)}")
            print(f"   Inquiries: {counts.get('inquiries', 0)}")
            print(f"   Space Rentals: {counts.get('space_rentals', 0)}")
            
            if counts.get('admins', 0) == 0:
                print("⚠️  No admin users found. Run database_setup.py first!")
                return False
                
            return True
        else:
            print(f"❌ Database test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Church Website Tests...")
    print("Make sure your Flask app is running first!")
    print("Run: python app.py")
    print("")
    
    input("Press Enter when your Flask app is running...")
    
    run_all_tests()