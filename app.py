from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import requests

from dotenv import load_dotenv
load_dotenv()
os.environ['BREVO_API_KEY']=os.getenv("BREVO_API_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///church.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads/events', exist_ok=True)
os.makedirs('static/uploads/gallery', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

db = SQLAlchemy(app)

SENDER_EMAIL = "elroypushparajah@gmail.com" # Your verified Brevo sender
RECIPIENT_EMAIL = [
    {"email": "elroypushparajah@gmail.com"},
    {"email": "theretechisform@gmail.com"}
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, folder='events'):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, unique_filename)
        file.save(filepath)

        # Return relative path for database storage
        return f"uploads/{folder}/{unique_filename}"
    return None


# Database Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    image_path = db.Column(db.String(500))  # Changed from image_url to image_path
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_date': self.event_date.strftime('%Y-%m-%d'),
            'image_path': self.image_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class SpaceRental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    space_requested = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    guest_count = db.Column(db.Integer, nullable=False)
    additional_needs = db.Column(db.Text)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'event_type': self.event_type,
            'space_requested': self.space_requested,
            'event_date': self.event_date.strftime('%Y-%m-%d'),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'guest_count': self.guest_count,
            'additional_needs': self.additional_needs,
            'message': self.message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'note': self.note,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


# Routes for main website
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/events')
def get_events():
    try:
        events = Event.query.order_by(Event.event_date.desc()).all()
        return jsonify([event.to_dict() for event in events])
    except Exception as e:
        print(f"Error getting events: {e}")
        return jsonify({'error': 'Failed to fetch events'}), 500


@app.route('/submit_inquiry', methods=['POST'])
def submit_inquiry():
    try:
        data = request.get_json()

        new_inquiry = Inquiry(
            name=data['name'],
            phone=data['phone'],
            email=data['email'],
            note=data['note']
        )

        db.session.add(new_inquiry)
        db.session.commit()


        # Prepare email content
        subject = f"New Inquiry from {data['name']}"
        body = f"""
                📩 New Inquiry Received

                Name: {data['name']}
                Phone: {data['phone']}
                Email: {data['email']}
                Note: {data['note']}
                """

        # Send email via Brevo API
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            },
            json={
                "sender": {"name": "Inquiry from CRC Application", "email": SENDER_EMAIL},
                "to": [{"email": RECIPIENT_EMAIL}],
                "subject": subject,
                "textContent": body
            }
        )

        if response.status_code not in [200, 201, 202]:
            print("❌ Brevo API Error:", response.text)

        return jsonify({'success': True, 'message': 'Inquiry saved and email sent!'})

    except Exception as e:
        print(f"Error submitting inquiry: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/space-rental', methods=['POST'])
def submit_space_rental():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['name', 'phone', 'email', 'event_type', 'space_requested',
                           'event_date', 'start_time', 'end_time', 'guest_count']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        rental = SpaceRental(
            name=data['name'],
            phone=data['phone'],
            email=data['email'],
            event_type=data['event_type'],
            space_requested=data['space_requested'],
            event_date=datetime.strptime(data['event_date'], '%Y-%m-%d').date(),
            start_time=data['start_time'],
            end_time=data['end_time'],
            guest_count=int(data['guest_count']),
            additional_needs=data.get('additional_needs', ''),
            message=data.get('message', '')
        )

        db.session.add(rental)
        db.session.commit()

        subject = f"New Space Rental Request from {data['name']}"
        body = f"""
                📌 New Space Rental Request

                Name: {data['name']}
                Phone: {data['phone']}
                Email: {data['email']}
                Event Type: {data['event_type']}
                Space Requested: {data['space_requested']}
                Event Date: {data['event_date']}
                Start Time: {data['start_time']}
                End Time: {data['end_time']}
                Guest Count: {data['guest_count']}
                Additional Needs: {data.get('additional_needs', 'None')}
                Message: {data.get('message', 'None')}
                """

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            },
            json={
                "sender": {"name": "Space Rental Request from CRC", "email": SENDER_EMAIL},
                "to": RECIPIENT_EMAIL,  # multiple recipients supported
                "subject": subject,
                "textContent": body
            }
        )

        if response.status_code not in [200, 201, 202]:
            print("❌ Brevo API Error:", response.text)

        # ----------------------------------------------------

        return jsonify({'message': 'Space rental request submitted successfully'}), 201

    except ValueError as e:
        print(f"Value error in space rental: {e}")
        return jsonify({'error': 'Invalid date format or guest count'}), 400
    except Exception as e:
        print(f"Error submitting space rental: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit space rental request'}), 500


# Admin Routes
@app.route('/admin')
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')


@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('admin_login'))

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password_hash, password):
            session.permanent = False
            session['admin_id'] = admin.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('admin_login'))

    except Exception as e:
        print(f"Login error: {e}")
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('admin_login'))


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        events = Event.query.order_by(Event.event_date.desc()).all()
        inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(10).all()
        rentals = SpaceRental.query.order_by(SpaceRental.created_at.desc()).limit(5).all()

        return render_template('admin_dashboard.html', events=events, inquiries=inquiries, rentals=rentals)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('admin_login'))


@app.route('/admin/events')
def admin_events():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        events = Event.query.order_by(Event.event_date.desc()).all()
        return render_template('admin_events.html', events=events)
    except Exception as e:
        print(f"Events error: {e}")
        flash('Error loading events', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/events/add')
def admin_add_event():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_add_event.html')


@app.route('/admin/events/add', methods=['POST'])
def admin_add_event_post():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        title = request.form.get('title')
        description = request.form.get('description')
        event_date_str = request.form.get('event_date')

        if not all([title, description, event_date_str]):
            flash('All fields are required', 'error')
            return redirect(url_for('admin_add_event'))

        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()

        # Handle file upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_path = save_uploaded_file(file, 'events')

        event = Event(
            title=title,
            description=description,
            event_date=event_date,
            image_path=image_path
        )

        db.session.add(event)
        db.session.commit()

        flash('Event added successfully!', 'success')
        return redirect(url_for('admin_events'))

    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('admin_add_event'))
    except Exception as e:
        print(f"Add event error: {e}")
        db.session.rollback()
        flash('Error adding event', 'error')
        return redirect(url_for('admin_add_event'))


@app.route('/admin/events/edit/<int:event_id>')
def admin_edit_event(event_id):
    if 'admin_id' not in session:
        flash('Please log in to access admin features', 'error')
        return redirect(url_for('admin_login'))

    try:
        print(f"Attempting to load event ID: {event_id}")  # Debug log
        event = Event.query.get(event_id)
        if not event:
            print(f"No event found for ID: {event_id}")  # Debug log
            flash(f'Event with ID {event_id} not found. It may have been deleted.', 'error')
            return redirect(url_for('admin_events'))

        print(f"Event loaded: ID={event.id}, Title={event.title}, Date={event.event_date}")  # Debug log
        return render_template('admin_edit_event.html', event=event)
    except Exception as e:
        print(f"Error loading event ID {event_id}: {str(e)}")  # Detailed error log
        flash(f'Error loading event: {str(e)}', 'error')
        return redirect(url_for('admin_events'))


@app.route('/admin/events/edit/<int:event_id>', methods=['POST'])
def admin_edit_event_post(event_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        event = Event.query.get(event_id)
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('admin_events'))

        title = request.form.get('title')
        description = request.form.get('description')
        event_date_str = request.form.get('event_date')

        if not all([title, description, event_date_str]):
            flash('All fields are required', 'error')
            return redirect(url_for('admin_edit_event', event_id=event_id))

        event.title = title
        event.description = description
        event.event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()

        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                # Delete old image if exists
                if event.image_path:
                    old_image_path = os.path.join('static', event.image_path)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except Exception as e:
                            print(f"Error deleting old image: {e}")

                # Save new image
                event.image_path = save_uploaded_file(file, 'events')

        db.session.commit()

        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_events'))

    except ValueError as e:
        flash('Invalid date format', 'error')
        print(f"Date error: {e}")
        return redirect(url_for('admin_edit_event', event_id=event_id))
    except Exception as e:
        print(f"Update event error: {e}")
        db.session.rollback()
        flash('Error updating event', 'error')
        return redirect(url_for('admin_edit_event', event_id=event_id))


@app.route('/admin/events/delete/<int:event_id>')
def admin_delete_event(event_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        event = Event.query.get_or_404(event_id)

        # Delete associated image file
        if event.image_path:
            image_path = os.path.join('static', event.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(event)
        db.session.commit()

        flash('Event deleted successfully!', 'success')
        return redirect(url_for('admin_events'))

    except Exception as e:
        print(f"Delete event error: {e}")
        db.session.rollback()
        flash('Error deleting event', 'error')
        return redirect(url_for('admin_events'))

@app.route('/admin/sermons')
def admin_sermons():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    return render_template('admin_sermons.html')

@app.route('/admin/sermons/add', methods=['GET', 'POST'])
def admin_add_sermon():
    if request.method == 'POST':
        # handle form submission
        pass
    return render_template('admin_add_sermon.html')

@app.route('/admin/sermons/edit/<int:sermon_id>', methods=['GET', 'POST'])
def admin_edit_sermon(sermon_id):
    #sermon = Sermon.query.get_or_404(sermon_id)
    if request.method == 'POST':
        # update sermon
        pass
    return render_template('admin_edit_sermon.html')

@app.route('/admin/sermons/delete/<int:sermon_id>', methods=['POST', 'GET'])
def admin_delete_sermon(sermon_id):
    #sermon = Sermon.query.get_or_404(sermon_id)

    # delete associated files if any
    # delete record from DB
    pass

    flash('Sermon deleted successfully', 'success')
    return redirect(url_for('admin_sermons'))



@app.route('/admin/space-rentals')
def admin_space_rentals():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    try:
        rentals = SpaceRental.query.order_by(SpaceRental.created_at.desc()).all()
        return render_template('admin_space_rentals.html', rentals=rentals)
    except Exception as e:
        print(f"Space rentals error: {e}")
        flash('Error loading space rentals', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin_inquiries')
def admin_inquiries():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin_inquiries.html', inquiries=inquiries)


# Test route to check database connection
@app.route('/api/test')
def test_database():
    try:
        # Test database connection
        admin_count = Admin.query.count()
        event_count = Event.query.count()
        inquiry_count = Inquiry.query.count()
        rental_count = SpaceRental.query.count()

        return jsonify({
            'status': 'success',
            'message': 'Database connection working',
            'counts': {
                'admins': admin_count,
                'events': event_count,
                'inquiries': inquiry_count,
                'space_rentals': rental_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)