from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
from functools import wraps
import hmac
import os
import re
import secrets
import uuid
import requests

from dotenv import load_dotenv
load_dotenv()

# ── Supabase config ──────────────────────────────────────────────────────────
SUPABASE_URL     = os.getenv("SUPABASE_URL")
SUPABASE_KEY     = os.getenv("SUPABASE_SERVICE_KEY")   # service key → used on backend only
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY']          = os.getenv('SECRET_KEY')
app.config['MAX_CONTENT_LENGTH']  = 16 * 1024 * 1024   # 16 MB
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'

if not app.config['SECRET_KEY']:
    raise RuntimeError('SECRET_KEY must be configured')


@app.url_defaults
def version_static_assets(endpoint, values):
    """Keep a browser's CSS and JavaScript in sync with the deployed template."""
    if endpoint == 'static' and 'filename' in values:
        asset_path = os.path.join(app.static_folder, values['filename'])
        if os.path.isfile(asset_path):
            values.setdefault('v', os.stat(asset_path).st_mtime_ns)

# ── Jinja2 filters ───────────────────────────────────────────────────────────
@app.template_filter('datetimeformat')
def datetimeformat(value, fmt='%d %b %Y %H:%M'):
    if not value:
        return ''
    if isinstance(value, datetime):
        return value.strftime(fmt)
    s = str(value)[:19].replace('T', ' ')   # handles '2026-02-10T20:23:00+00:00'
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S').strftime(fmt)
    except ValueError:
        pass
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').strftime(fmt)
    except ValueError:
        pass
    return str(value)

@app.template_filter('dateformat')
def dateformat(value, fmt='%d %b %Y'):
    return datetimeformat(value, fmt)


@app.template_filter('admindatetime')
def admin_datetime(value):
    if not value:
        return 'Date unavailable'
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%d %b %Y · %H:%M')
    except (ValueError, TypeError):
        return 'Date unavailable'


@app.template_filter('eventimage')
def event_image(value):
    value = str(value or '')
    if value.startswith('uploads/'):
        return url_for('static', filename=value)
    if value.startswith('/static/') or value.startswith('https://'):
        return value
    return ''

# ── Constants ────────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
STORAGE_BUCKET     = 'church-uploads'   # Supabase Storage bucket name

SENDER_EMAIL = "elroypushparajah@gmail.com"
RECIPIENT_EMAIL = [
    {"email": "elroypushparajah@gmail.com"},
    {"email": "nathanael.somanathan@gmail.com"},
    {"email": "ernestnava@gmail.com"}
]
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


# ── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def required_text(data, field, max_length):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field.replace("_", " ").title()} is required')

    value = value.strip()
    if len(value) > max_length:
        raise ValueError(
            f'{field.replace("_", " ").title()} must be {max_length} characters or fewer'
        )
    return value


def validated_email(data):
    email = required_text(data, 'email', 254)
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError('A valid email address is required')
    return email


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return view(*args, **kwargs)

    return wrapped


def csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {'csrf_token': csrf_token}


@app.before_request
def protect_admin_posts():
    if request.method != 'POST' or not request.path.startswith('/admin'):
        return None

    submitted = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
    expected = session.get('_csrf_token', '')
    if not submitted or not expected or not hmac.compare_digest(submitted, expected):
        return jsonify({'error': 'Invalid or expired form token'}), 400

    return None


@app.after_request
def add_security_headers(response):
    if response.mimetype == 'text/html':
        response.headers['Cache-Control'] = 'no-store' if request.path.startswith('/admin') else 'no-cache'
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault(
        'Permissions-Policy',
        'camera=(), microphone=(), geolocation=()',
    )
    if request.is_secure:
        response.headers.setdefault(
            'Strict-Transport-Security',
            'max-age=31536000; includeSubDomains',
        )
    return response


def send_brevo_email(sender_name, subject, body):
    """Send a notification and return whether Brevo accepted it."""
    if not BREVO_API_KEY:
        print("Brevo notification skipped: BREVO_API_KEY is not configured")
        return False

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json",
            },
            json={
                "sender": {"name": sender_name, "email": SENDER_EMAIL},
                "to": RECIPIENT_EMAIL,
                "subject": subject,
                "textContent": body,
            },
            timeout=15,
        )
    except requests.RequestException as error:
        print(f"Brevo notification request failed: {error}")
        return False

    if response.status_code not in (200, 201, 202):
        print(
            "Brevo notification rejected "
            f"with HTTP status {response.status_code}: {response.text[:500]}"
        )
        return False

    return True


def save_uploaded_file(file, folder='events'):
    """Upload file to Supabase Storage and return the public URL."""
    if file and file.filename:
        if not allowed_file(file.filename):
            raise ValueError('Choose a JPG, PNG, GIF or WebP image.')
        filename      = secure_filename(file.filename)
        name, ext     = os.path.splitext(filename)
        unique_name   = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        storage_path  = f"{folder}/{unique_name}"                  # e.g. events/photo_abc123.jpg
        content_type = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                        'png': 'image/png', 'gif': 'image/gif',
                        'webp': 'image/webp'}[ext.lstrip('.').lower()]

        file_bytes = file.read(8 * 1024 * 1024 + 1)
        if not file_bytes or len(file_bytes) > 8 * 1024 * 1024:
            raise ValueError('Choose an image no larger than 8 MB.')
        signatures = {
            'image/jpeg': file_bytes.startswith(b'\xff\xd8\xff'),
            'image/png': file_bytes.startswith(b'\x89PNG\r\n\x1a\n'),
            'image/gif': file_bytes.startswith((b'GIF87a', b'GIF89a')),
            'image/webp': file_bytes.startswith(b'RIFF') and file_bytes[8:12] == b'WEBP',
        }
        if not signatures[content_type]:
            raise ValueError('The selected file does not match its image type.')

        supabase.storage.from_(STORAGE_BUCKET).upload(
            storage_path,
            file_bytes,
            file_options={"content-type": content_type},
        )

        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
        return public_url   # full https:// URL — store this in the DB

    return None


def _delete_storage_file(public_url):
    """Delete a file from Supabase Storage given its public URL."""
    if not public_url:
        return
    try:
        # Extract the path after the bucket name in the URL
        # URL format: https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
        marker = f"/object/public/{STORAGE_BUCKET}/"
        if marker in public_url:
            storage_path = public_url.split(marker)[1]
            supabase.storage.from_(STORAGE_BUCKET).remove([storage_path])
    except Exception as e:
        print(f"Warning: could not delete storage file: {e}")


# ── Public routes ────────────────────────────────────────────────────────────
def cleanup_unreferenced_event_image(image_url):
    """Do not remove an upload if an uncertain database response saved its URL."""
    if not image_url:
        return
    try:
        references = supabase.table('events').select('id').eq('image_path', image_url).limit(1).execute().data
        if not references:
            _delete_storage_file(image_url)
    except Exception:
        # Keep the file if the database is unavailable; a later cleanup can retry.
        app.logger.warning('Could not verify an event upload for cleanup; file retained.')


def validate_event_date(value):
    try:
        datetime.strptime(value or '', '%Y-%m-%d')
    except ValueError:
        raise ValueError('Choose a valid event date.') from None


@app.route('/')
@app.route('/<page_id>')
def home(page_id='home'):
    public_pages = {'home', 'about', 'events', 'space-rentals', 'sermons', 'ministries'}
    current_page = page_id if page_id in public_pages else 'home'
    return render_template('index.html', current_page=current_page)


@app.route('/api/events')
def get_events():
    try:
        result = (
            supabase.table('events')
            .select('*')
            .order('event_date', desc=True)
            .execute()
        )
        return jsonify(result.data)
    except Exception as e:
        print(f"Error getting events: {e}")
        return jsonify({'error': 'Failed to fetch events'}), 500


@app.route('/submit_inquiry', methods=['POST'])
def submit_inquiry():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid request'}), 400

        name = required_text(data, 'name', 120)
        phone = required_text(data, 'phone', 40)
        email = validated_email(data)
        note = required_text(data, 'note', 3000)

        supabase.table('inquiries').insert({
            'name': name,
            'phone': phone,
            'email': email,
            'note': note,
        }).execute()

        # Email via Brevo (unchanged)
        subject = f"DCC: New Inquiry from {name}"
        body    = (
            f"📩 New Inquiry Received\n\n"
            f"Name:  {name}\n"
            f"Phone: {phone}\n"
            f"Email: {email}\n"
            f"Note:  {note}"
        )

        email_sent = send_brevo_email(
            "Inquiry from CRC Application",
            subject,
            body,
        )

        if not email_sent:
            return jsonify({
                'success': True,
                'saved': True,
                'email_sent': False,
                'message': (
                    'Your inquiry was received and saved. The email notification '
                    'could not be sent, but the church team can still view your '
                    'inquiry in the admin panel.'
                ),
            }), 202

        return jsonify({
            'success': True,
            'saved': True,
            'email_sent': True,
            'message': 'Your inquiry was received and the church team was notified.',
        })

    except ValueError as error:
        return jsonify({'success': False, 'error': str(error)}), 400
    except Exception as e:
        print(f"Error submitting inquiry: {e}")
        return jsonify({
            'success': False,
            'error': 'The inquiry could not be saved. Please try again.',
        }), 500


@app.route('/api/space-rental', methods=['POST'])
def submit_space_rental():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'No data provided'}), 400

        required_fields = [
            'name', 'phone', 'email', 'event_type', 'space_requested',
            'event_date', 'start_time', 'end_time', 'guest_count',
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        name = required_text(data, 'name', 120)
        phone = required_text(data, 'phone', 40)
        email = validated_email(data)
        event_type = required_text(data, 'event_type', 120)
        space_requested = required_text(data, 'space_requested', 120)
        additional_needs = str(data.get('additional_needs', '')).strip()[:1000]
        message = str(data.get('message', '')).strip()[:3000]
        guest_count = int(data['guest_count'])
        if guest_count < 1 or guest_count > 250:
            raise ValueError('Guest count must be between 1 and 250')
        datetime.strptime(data['event_date'], '%Y-%m-%d')
        datetime.strptime(data['start_time'], '%H:%M')
        datetime.strptime(data['end_time'], '%H:%M')
        if data['end_time'] <= data['start_time']:
            raise ValueError('End time must be after start time')

        supabase.table('space_rentals').insert({
            'name':             name,
            'phone':            phone,
            'email':            email,
            'event_type':       event_type,
            'space_requested':  space_requested,
            'event_date':       data['event_date'],          # expects 'YYYY-MM-DD' string
            'start_time':       data['start_time'],
            'end_time':         data['end_time'],
            'guest_count':      guest_count,
            'additional_needs': additional_needs,
            'message':          message,
        }).execute()

        # Email via Brevo (unchanged)
        subject = f"DCC: New Space Rental Request from {name}"
        body    = (
            f"📌 New Space Rental Request\n\n"
            f"Name:             {name}\n"
            f"Phone:            {phone}\n"
            f"Email:            {email}\n"
            f"Event Type:       {event_type}\n"
            f"Space Requested:  {space_requested}\n"
            f"Event Date:       {data['event_date']}\n"
            f"Start Time:       {data['start_time']}\n"
            f"End Time:         {data['end_time']}\n"
            f"Guest Count:      {guest_count}\n"
            f"Additional Needs: {additional_needs or 'None'}\n"
            f"Message:          {message or 'None'}"
        )

        email_sent = send_brevo_email(
            "Space Rental Request from CRC",
            subject,
            body,
        )

        if not email_sent:
            return jsonify({
                'success': True,
                'saved': True,
                'email_sent': False,
                'message': (
                    'Your rental request was received and saved. The email '
                    'notification could not be sent, but the church team can '
                    'still view your request in the admin panel.'
                ),
            }), 202

        return jsonify({
            'success': True,
            'saved': True,
            'email_sent': True,
            'message': (
                'Your rental request was received and the church team was notified.'
            ),
        }), 201

    except ValueError as error:
        return jsonify({'success': False, 'error': str(error)}), 400
    except Exception as e:
        print(f"Error submitting space rental: {e}")
        return jsonify({'error': 'Failed to submit space rental request'}), 500


# ── Admin: auth ──────────────────────────────────────────────────────────────

@app.route('/admin')
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_signin.html')


@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('admin_login'))

        result = (
            supabase.table('admins')
            .select('*')
            .eq('username', username)
            .maybe_single()       # returns None instead of raising if no row found
            .execute()
        )
        admin = result.data

        if admin and check_password_hash(admin['password_hash'], password):
            session.permanent = False
            session['admin_id'] = admin['id']
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


# ── Admin: dashboard ─────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        events    = supabase.table('events').select('*').order('created_at', desc=True).limit(5).execute().data
        inquiries = supabase.table('inquiries').select('*').order('created_at', desc=True).limit(5).execute().data
        rentals   = supabase.table('space_rentals').select('*').order('created_at', desc=True).limit(5).execute().data

        totals = {
            key: supabase.table(table).select('id', count='exact', head=True).execute().count
            for key, table in [('events', 'events'), ('inquiries', 'inquiries'), ('rentals', 'space_rentals')]
        }
        return render_template('admin_overview.html', events=events or [],
                               inquiries=inquiries or [], rentals=rentals or [], totals=totals)
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('admin_overview.html', events=[], inquiries=[],
                               rentals=[], totals={}, load_error=True), 503


# ── Admin: events ────────────────────────────────────────────────────────────

@app.route('/admin/events')
@admin_required
def admin_events():
    try:
        events = supabase.table('events').select('*').order('event_date', desc=True).execute().data
        return render_template('admin_event_list.html', events=events or [])
    except Exception as e:
        print(f"Events error: {e}")
        return render_template('admin_event_list.html', events=[], load_error=True), 503


@app.route('/admin/events/add')
@admin_required
def admin_add_event():
    return render_template('admin_event_form.html', event=None, editing=False)


@app.route('/admin/events/add', methods=['POST'])
@admin_required
def admin_add_event_post():
    image_url = None
    try:
        title          = required_text(request.form, 'title', 180)
        description    = required_text(request.form, 'description', 10000)
        event_date_str = request.form.get('event_date')

        if not all([title, description, event_date_str]):
            raise ValueError('Title, date and description are required.')

        # Validate date format
        validate_event_date(event_date_str)

        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_url = save_uploaded_file(file, 'events')

        supabase.table('events').insert({
            'title':       title,
            'description': description,
            'event_date':  event_date_str,
            'image_path':  image_url,     # full Supabase Storage URL (or None)
        }).execute()

        flash('Event added successfully!', 'success')
        return redirect(url_for('admin_events'))

    except ValueError as error:
        if image_url:
            cleanup_unreferenced_event_image(image_url)
        flash(str(error), 'error')
        return render_template('admin_event_form.html', event=request.form,
                               editing=False), 400
    except Exception as e:
        print(f"Add event error: {e}")
        if image_url:
            cleanup_unreferenced_event_image(image_url)
        flash('The event could not be saved. Your text has been kept; please reselect the image and try again.', 'error')
        return render_template('admin_event_form.html', event=request.form,
                               editing=False), 503


@app.route('/admin/events/edit/<int:event_id>')
@admin_required
def admin_edit_event(event_id):
    try:
        result = (
            supabase.table('events')
            .select('*')
            .eq('id', event_id)
            .maybe_single()
            .execute()
        )
        event = result.data
        if not event:
            flash(f'Event with ID {event_id} not found.', 'error')
            return redirect(url_for('admin_events'))

        return render_template('admin_event_form.html', event=event, editing=True)
    except Exception as e:
        print(f"Error loading event {event_id}: {e}")
        flash('The event could not be loaded. Please try again.', 'error')
        return redirect(url_for('admin_events'))


@app.route('/admin/events/edit/<int:event_id>', methods=['POST'])
@admin_required
def admin_edit_event_post(event_id):
    new_image = None
    event = None
    try:
        # Fetch current event so we can delete old image if needed
        result = (
            supabase.table('events')
            .select('*')
            .eq('id', event_id)
            .maybe_single()
            .execute()
        )
        event = result.data
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('admin_events'))

        title          = required_text(request.form, 'title', 180)
        description    = required_text(request.form, 'description', 10000)
        event_date_str = request.form.get('event_date')

        if not all([title, description, event_date_str]):
            raise ValueError('Title, date and description are required.')

        validate_event_date(event_date_str)

        updates = {
            'title':       title,
            'description': description,
            'event_date':  event_date_str,
        }

        # Handle new image upload
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                new_image = save_uploaded_file(file, 'events')
                updates['image_path'] = new_image

        supabase.table('events').update(updates).eq('id', event_id).execute()
        if new_image:
            _delete_storage_file(event.get('image_path'))

        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_events'))

    except ValueError as error:
        if new_image:
            cleanup_unreferenced_event_image(new_image)
        flash(str(error), 'error')
        values = dict(event or {})
        values.update(request.form)
        return render_template('admin_event_form.html', event=values, editing=True), 400
    except Exception as e:
        print(f"Update event error: {e}")
        if new_image:
            cleanup_unreferenced_event_image(new_image)
        flash('Changes could not be saved. Your text has been kept; please reselect any new image and try again.', 'error')
        values = dict(event or {})
        values.update(request.form)
        return render_template('admin_event_form.html', event=values, editing=True), 503


@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    try:
        # Fetch event to get image URL before deleting
        result = (
            supabase.table('events')
            .select('image_path')
            .eq('id', event_id)
            .maybe_single()
            .execute()
        )
        event = result.data
        supabase.table('events').delete().eq('id', event_id).execute()
        if event:
            _delete_storage_file(event.get('image_path'))

        flash('Event deleted successfully!', 'success')
        return redirect(url_for('admin_events'))

    except Exception as e:
        print(f"Delete event error: {e}")
        flash('Error deleting event', 'error')
        return redirect(url_for('admin_events'))


# ── Admin: sermons (stub — unchanged) ────────────────────────────────────────

@app.route('/admin/sermons')
@admin_required
def admin_sermons():
    return render_template('admin_sermon_workspace.html')


@app.route('/admin/sermons/add', methods=['GET', 'POST'])
@admin_required
def admin_add_sermon():
    return render_template('admin_sermon_workspace.html'), 503


@app.route('/admin/sermons/edit/<int:sermon_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_sermon(sermon_id):
    return render_template('admin_sermon_workspace.html'), 503


@app.route('/admin/sermons/delete/<int:sermon_id>', methods=['POST'])
@admin_required
def admin_delete_sermon(sermon_id):
    return render_template('admin_sermon_workspace.html'), 503


# ── Admin: space rentals ─────────────────────────────────────────────────────

@app.route('/admin/space-rentals')
@admin_required
def admin_space_rentals():
    try:
        rentals = (
            supabase.table('space_rentals')
            .select('*')
            .order('created_at', desc=True)
            .execute()
            .data
        )
        return render_template('admin_rental_list.html', rentals=rentals or [])
    except Exception as e:
        print(f"Space rentals error: {e}")
        return render_template('admin_rental_list.html', rentals=[], load_error=True), 503


# ── Admin: inquiries ─────────────────────────────────────────────────────────

@app.route('/admin_inquiries')
@admin_required
def admin_inquiries():
    try:
        inquiries = supabase.table('inquiries').select('*').order('created_at', desc=True).execute().data
        return render_template('admin_message_list.html', inquiries=inquiries or [])
    except Exception as error:
        print(f'Inquiries error: {error}')
        return render_template('admin_message_list.html', inquiries=[], load_error=True), 503


# ── Debug / health-check ─────────────────────────────────────────────────────

@app.route('/api/test')
def test_database():
    try:
        supabase.table('events').select('id').limit(1).execute()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Health check failed: {e}")
        return jsonify({'status': 'unavailable'}), 503


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '').lower() == 'true')





# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import check_password_hash
# from werkzeug.utils import secure_filename
# from datetime import datetime
# import os
# import uuid
# import requests
#
# from dotenv import load_dotenv
# load_dotenv()
# os.environ['BREVO_API_KEY']=os.getenv("BREVO_API_KEY")
# BREVO_API_KEY = os.getenv("BREVO_API_KEY")
#
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///church.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#
# # File upload configuration
# app.config['UPLOAD_FOLDER'] = 'static/uploads'
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
#
# # Create upload directories if they don't exist
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# os.makedirs('static/uploads/events', exist_ok=True)
# os.makedirs('static/uploads/gallery', exist_ok=True)
# os.makedirs('static/images', exist_ok=True)
#
# db = SQLAlchemy(app)
#
# SENDER_EMAIL = "elroypushparajah@gmail.com" # Your verified Brevo sender
# RECIPIENT_EMAIL = [
#     {"email": "elroypushparajah@gmail.com"},
#     {"email": "theretechisform@gmail.com"}
# ]
#
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#
#
# def save_uploaded_file(file, folder='events'):
#     """Save uploaded file and return filename"""
#     if file and allowed_file(file.filename):
#         # Generate unique filename
#         filename = secure_filename(file.filename)
#         name, ext = os.path.splitext(filename)
#         unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
#
#         # Save file
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, unique_filename)
#         file.save(filepath)
#
#         # Return relative path for database storage
#         return f"uploads/{folder}/{unique_filename}"
#     return None
#
#
# # Database Models
# class Admin(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     password_hash = db.Column(db.String(200), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#
# class Event(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(200), nullable=False)
#     description = db.Column(db.Text, nullable=False)
#     event_date = db.Column(db.Date, nullable=False)
#     image_path = db.Column(db.String(500))  # Changed from image_url to image_path
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'title': self.title,
#             'description': self.description,
#             'event_date': self.event_date.strftime('%Y-%m-%d'),
#             'image_path': self.image_path,
#             'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
#         }
#
#
# class SpaceRental(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     phone = db.Column(db.String(20), nullable=False)
#     email = db.Column(db.String(100), nullable=False)
#     event_type = db.Column(db.String(100), nullable=False)
#     space_requested = db.Column(db.String(100), nullable=False)
#     event_date = db.Column(db.Date, nullable=False)
#     start_time = db.Column(db.String(20), nullable=False)
#     end_time = db.Column(db.String(20), nullable=False)
#     guest_count = db.Column(db.Integer, nullable=False)
#     additional_needs = db.Column(db.Text)
#     message = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'name': self.name,
#             'phone': self.phone,
#             'email': self.email,
#             'event_type': self.event_type,
#             'space_requested': self.space_requested,
#             'event_date': self.event_date.strftime('%Y-%m-%d'),
#             'start_time': self.start_time,
#             'end_time': self.end_time,
#             'guest_count': self.guest_count,
#             'additional_needs': self.additional_needs,
#             'message': self.message,
#             'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
#         }
#
#
# class Inquiry(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     phone = db.Column(db.String(20), nullable=False)
#     email = db.Column(db.String(100), nullable=False)
#     note = db.Column(db.Text, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'name': self.name,
#             'phone': self.phone,
#             'email': self.email,
#             'note': self.note,
#             'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
#         }
#
#
# # Routes for main website
# @app.route('/')
# def home():
#     return render_template('index.html')
#
#
# @app.route('/static/uploads/<path:filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
#
# # @app.route("/about")
# # def about():
# #     return render_template("about.html")
#
# @app.route('/api/events')
# def get_events():
#     try:
#         events = Event.query.order_by(Event.event_date.desc()).all()
#         return jsonify([event.to_dict() for event in events])
#     except Exception as e:
#         print(f"Error getting events: {e}")
#         return jsonify({'error': 'Failed to fetch events'}), 500
#
#
# @app.route('/submit_inquiry', methods=['POST'])
# def submit_inquiry():
#     try:
#         data = request.get_json()
#
#         new_inquiry = Inquiry(
#             name=data['name'],
#             phone=data['phone'],
#             email=data['email'],
#             note=data['note']
#         )
#
#         db.session.add(new_inquiry)
#         db.session.commit()
#
#
#         # Prepare email content
#         subject = f"New Inquiry from {data['name']}"
#         body = f"""
#                 📩 New Inquiry Received
#
#                 Name: {data['name']}
#                 Phone: {data['phone']}
#                 Email: {data['email']}
#                 Note: {data['note']}
#                 """
#
#         # Send email via Brevo API
#         response = requests.post(
#             "https://api.brevo.com/v3/smtp/email",
#             headers={
#                 "accept": "application/json",
#                 "api-key": BREVO_API_KEY,
#                 "content-type": "application/json"
#             },
#             json={
#                 "sender": {"name": "Inquiry from CRC Application", "email": SENDER_EMAIL},
#                 "to": [{"email": RECIPIENT_EMAIL}],
#                 "subject": subject,
#                 "textContent": body
#             }
#         )
#
#         if response.status_code not in [200, 201, 202]:
#             print("❌ Brevo API Error:", response.text)
#
#         return jsonify({'success': True, 'message': 'Inquiry saved and email sent!'})
#
#     except Exception as e:
#         print(f"Error submitting inquiry: {str(e)}")
#         return jsonify({'success': False, 'error': str(e)}), 500
#
#
# @app.route('/api/space-rental', methods=['POST'])
# def submit_space_rental():
#     try:
#         data = request.get_json()
#
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400
#
#         # Validate required fields
#         required_fields = ['name', 'phone', 'email', 'event_type', 'space_requested',
#                            'event_date', 'start_time', 'end_time', 'guest_count']
#         for field in required_fields:
#             if field not in data or not data[field]:
#                 return jsonify({'error': f'Missing required field: {field}'}), 400
#
#         rental = SpaceRental(
#             name=data['name'],
#             phone=data['phone'],
#             email=data['email'],
#             event_type=data['event_type'],
#             space_requested=data['space_requested'],
#             event_date=datetime.strptime(data['event_date'], '%Y-%m-%d').date(),
#             start_time=data['start_time'],
#             end_time=data['end_time'],
#             guest_count=int(data['guest_count']),
#             additional_needs=data.get('additional_needs', ''),
#             message=data.get('message', '')
#         )
#
#         db.session.add(rental)
#         db.session.commit()
#
#         subject = f"New Space Rental Request from {data['name']}"
#         body = f"""
#                 📌 New Space Rental Request
#
#                 Name: {data['name']}
#                 Phone: {data['phone']}
#                 Email: {data['email']}
#                 Event Type: {data['event_type']}
#                 Space Requested: {data['space_requested']}
#                 Event Date: {data['event_date']}
#                 Start Time: {data['start_time']}
#                 End Time: {data['end_time']}
#                 Guest Count: {data['guest_count']}
#                 Additional Needs: {data.get('additional_needs', 'None')}
#                 Message: {data.get('message', 'None')}
#                 """
#
#         response = requests.post(
#             "https://api.brevo.com/v3/smtp/email",
#             headers={
#                 "accept": "application/json",
#                 "api-key": BREVO_API_KEY,
#                 "content-type": "application/json"
#             },
#             json={
#                 "sender": {"name": "Space Rental Request from CRC", "email": SENDER_EMAIL},
#                 "to": RECIPIENT_EMAIL,  # multiple recipients supported
#                 "subject": subject,
#                 "textContent": body
#             }
#         )
#
#         if response.status_code not in [200, 201, 202]:
#             print("❌ Brevo API Error:", response.text)
#
#         # ----------------------------------------------------
#
#         return jsonify({'message': 'Space rental request submitted successfully'}), 201
#
#     except ValueError as e:
#         print(f"Value error in space rental: {e}")
#         return jsonify({'error': 'Invalid date format or guest count'}), 400
#     except Exception as e:
#         print(f"Error submitting space rental: {e}")
#         db.session.rollback()
#         return jsonify({'error': 'Failed to submit space rental request'}), 500
#
#
# # Admin Routes
# @app.route('/admin')
# def admin_login():
#     if 'admin_id' in session:
#         return redirect(url_for('admin_dashboard'))
#     return render_template('admin_login.html')
#
#
# @app.route('/admin/login', methods=['POST'])
# def admin_login_post():
#     try:
#         username = request.form.get('username')
#         password = request.form.get('password')
#
#         if not username or not password:
#             flash('Username and password are required', 'error')
#             return redirect(url_for('admin_login'))
#
#         admin = Admin.query.filter_by(username=username).first()
#
#         if admin and check_password_hash(admin.password_hash, password):
#             session.permanent = False
#             session['admin_id'] = admin.id
#             flash('Login successful!', 'success')
#             return redirect(url_for('admin_dashboard'))
#         else:
#             flash('Invalid username or password', 'error')
#             return redirect(url_for('admin_login'))
#
#     except Exception as e:
#         print(f"Login error: {e}")
#         flash('Login failed. Please try again.', 'error')
#         return redirect(url_for('admin_login'))
#
#
# @app.route('/admin/logout')
# def admin_logout():
#     session.pop('admin_id', None)
#     flash('Logged out successfully', 'info')
#     return redirect(url_for('admin_login'))
#
#
# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     try:
#         events = Event.query.order_by(Event.event_date.desc()).all()
#         inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(10).all()
#         rentals = SpaceRental.query.order_by(SpaceRental.created_at.desc()).limit(5).all()
#
#         return render_template('admin_dashboard.html', events=events, inquiries=inquiries, rentals=rentals)
#     except Exception as e:
#         print(f"Dashboard error: {e}")
#         flash('Error loading dashboard', 'error')
#         return redirect(url_for('admin_login'))
#
#
# @app.route('/admin/events')
# def admin_events():
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     try:
#         events = Event.query.order_by(Event.event_date.desc()).all()
#         return render_template('admin_events.html', events=events)
#     except Exception as e:
#         print(f"Events error: {e}")
#         flash('Error loading events', 'error')
#         return redirect(url_for('admin_dashboard'))
#
#
# @app.route('/admin/events/add')
# def admin_add_event():
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#     return render_template('admin_add_event.html')
#
#
# @app.route('/admin/events/add', methods=['POST'])
# def admin_add_event_post():
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     try:
#         title = request.form.get('title')
#         description = request.form.get('description')
#         event_date_str = request.form.get('event_date')
#
#         if not all([title, description, event_date_str]):
#             flash('All fields are required', 'error')
#             return redirect(url_for('admin_add_event'))
#
#         event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
#
#         # Handle file upload
#         image_path = None
#         if 'image' in request.files:
#             file = request.files['image']
#             if file.filename != '':
#                 image_path = save_uploaded_file(file, 'events')
#
#         event = Event(
#             title=title,
#             description=description,
#             event_date=event_date,
#             image_path=image_path
#         )
#
#         db.session.add(event)
#         db.session.commit()
#
#         flash('Event added successfully!', 'success')
#         return redirect(url_for('admin_events'))
#
#     except ValueError:
#         flash('Invalid date format', 'error')
#         return redirect(url_for('admin_add_event'))
#     except Exception as e:
#         print(f"Add event error: {e}")
#         db.session.rollback()
#         flash('Error adding event', 'error')
#         return redirect(url_for('admin_add_event'))
#
#
# @app.route('/admin/events/edit/<int:event_id>')
# def admin_edit_event(event_id):
#     if 'admin_id' not in session:
#         flash('Please log in to access admin features', 'error')
#         return redirect(url_for('admin_login'))
#
#     try:
#         print(f"Attempting to load event ID: {event_id}")  # Debug log
#         event = Event.query.get(event_id)
#         if not event:
#             print(f"No event found for ID: {event_id}")  # Debug log
#             flash(f'Event with ID {event_id} not found. It may have been deleted.', 'error')
#             return redirect(url_for('admin_events'))
#
#         print(f"Event loaded: ID={event.id}, Title={event.title}, Date={event.event_date}")  # Debug log
#         return render_template('admin_edit_event.html', event=event)
#     except Exception as e:
#         print(f"Error loading event ID {event_id}: {str(e)}")  # Detailed error log
#         flash(f'Error loading event: {str(e)}', 'error')
#         return redirect(url_for('admin_events'))
#
#
# @app.route('/admin/events/edit/<int:event_id>', methods=['POST'])
# def admin_edit_event_post(event_id):
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     try:
#         event = Event.query.get(event_id)
#         if not event:
#             flash('Event not found', 'error')
#             return redirect(url_for('admin_events'))
#
#         title = request.form.get('title')
#         description = request.form.get('description')
#         event_date_str = request.form.get('event_date')
#
#         if not all([title, description, event_date_str]):
#             flash('All fields are required', 'error')
#             return redirect(url_for('admin_edit_event', event_id=event_id))
#
#         event.title = title
#         event.description = description
#         event.event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
#
#         # Handle file upload
#         if 'image' in request.files:
#             file = request.files['image']
#             if file.filename != '':
#                 # Delete old image if exists
#                 if event.image_path:
#                     old_image_path = os.path.join('static', event.image_path)
#                     if os.path.exists(old_image_path):
#                         try:
#                             os.remove(old_image_path)
#                         except Exception as e:
#                             print(f"Error deleting old image: {e}")
#
#                 # Save new image
#                 event.image_path = save_uploaded_file(file, 'events')
#
#         db.session.commit()
#
#         flash('Event updated successfully!', 'success')
#         return redirect(url_for('admin_events'))
#
#     except ValueError as e:
#         flash('Invalid date format', 'error')
#         print(f"Date error: {e}")
#         return redirect(url_for('admin_edit_event', event_id=event_id))
#     except Exception as e:
#         print(f"Update event error: {e}")
#         db.session.rollback()
#         flash('Error updating event', 'error')
#         return redirect(url_for('admin_edit_event', event_id=event_id))
#
#
# @app.route('/admin/events/delete/<int:event_id>')
# def admin_delete_event(event_id):
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     try:
#         event = Event.query.get_or_404(event_id)
#
#         # Delete associated image file
#         if event.image_path:
#             image_path = os.path.join('static', event.image_path)
#             if os.path.exists(image_path):
#                 os.remove(image_path)
#
#         db.session.delete(event)
#         db.session.commit()
#
#         flash('Event deleted successfully!', 'success')
#         return redirect(url_for('admin_events'))
#
#     except Exception as e:
#         print(f"Delete event error: {e}")
#         db.session.rollback()
#         flash('Error deleting event', 'error')
#         return redirect(url_for('admin_events'))
#
# @app.route('/admin/sermons')
# def admin_sermons():
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     return render_template('admin_sermons.html')
#
# @app.route('/admin/sermons/add', methods=['GET', 'POST'])
# def admin_add_sermon():
#     if request.method == 'POST':
#         # handle form submission
#         pass
#     return render_template('admin_add_sermon.html')
#
# @app.route('/admin/sermons/edit/<int:sermon_id>', methods=['GET', 'POST'])
# def admin_edit_sermon(sermon_id):
#     #sermon = Sermon.query.get_or_404(sermon_id)
#     if request.method == 'POST':
#         # update sermon
#         pass
#     return render_template('admin_edit_sermon.html')
#
# @app.route('/admin/sermons/delete/<int:sermon_id>', methods=['POST', 'GET'])
# def admin_delete_sermon(sermon_id):
#     #sermon = Sermon.query.get_or_404(sermon_id)
#
#     # delete associated files if any
#     # delete record from DB
#     pass
#
#     flash('Sermon deleted successfully', 'success')
#     return redirect(url_for('admin_sermons'))
#
#
#
# @app.route('/admin/space-rentals')
# def admin_space_rentals():
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     try:
#         rentals = SpaceRental.query.order_by(SpaceRental.created_at.desc()).all()
#         return render_template('admin_space_rentals.html', rentals=rentals)
#     except Exception as e:
#         print(f"Space rentals error: {e}")
#         flash('Error loading space rentals', 'error')
#         return redirect(url_for('admin_dashboard'))
#
#
# @app.route('/admin_inquiries')
# def admin_inquiries():
#     if 'admin_id' not in session:
#         return redirect(url_for('admin_login'))
#
#     inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
#     return render_template('admin_inquiries.html', inquiries=inquiries)
#
#
# # Test route to check database connection
# @app.route('/api/test')
# def test_database():
#     try:
#         # Test database connection
#         admin_count = Admin.query.count()
#         event_count = Event.query.count()
#         inquiry_count = Inquiry.query.count()
#         rental_count = SpaceRental.query.count()
#
#         return jsonify({
#             'status': 'success',
#             'message': 'Database connection working',
#             'counts': {
#                 'admins': admin_count,
#                 'events': event_count,
#                 'inquiries': inquiry_count,
#                 'space_rentals': rental_count
#             }
#         })
#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': str(e)
#         }), 500
#
#
# if __name__ == '__main__':
#     app.run(debug=True)
