// Preloader
window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    const progressFill = document.getElementById('progress-fill');

    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            setTimeout(() => {
                preloader.classList.add('hidden');
                initializeAnimations();
            }, 500);
        }
        progressFill.style.width = `${progress}%`;
    }, 100);

    // Fallback: Hide preloader after 5 seconds
    setTimeout(hidePreloader, 5000);

    function hidePreloader() {
        clearInterval(interval);
        preloader.classList.add('hidden');
        console.log('Preloader hidden');
        initializeAnimations();
        // Ensure home page is visible
        const homePage = document.getElementById('home');
        if (homePage) {
            homePage.classList.add('active');
            homePage.style.opacity = '1';
            homePage.style.transform = 'translateY(0)';
        }
    }
});

// Create floating particles (optimized for performance)
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = window.innerWidth < 768 ? 20 : 50; // Reduce particles on mobile
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.width = particle.style.height = `${Math.random() * 4 + 2}px`;
        particle.style.animationDelay = `${Math.random() * 8}s`;
        particle.style.animationDuration = `${Math.random() * 4 + 4}s`;
        particlesContainer.appendChild(particle);
    }
}

// Initialize animations
function initializeAnimations() {
    createParticles();
    initializeScrollAnimations();
    initializeNavbarAnimation();
}

// Scroll animations
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .scale-in').forEach(el => {
        observer.observe(el);
    });
}

// Navbar animation on scroll
function initializeNavbarAnimation() {
    const navbar = document.getElementById('navbar');

    function handleScroll() {
        if (window.innerWidth > 768) {
            navbar.classList.toggle('scrolled', window.scrollY > 100);
        } else {
            navbar.classList.remove('scrolled');
        }
    }

    // Listen to scroll
    window.addEventListener('scroll', handleScroll);

    // Listen to resize to handle switching between mobile/desktop
    window.addEventListener('resize', handleScroll);
}


// Page navigation with animation
function showPage(pageId) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));

    const currentPage = document.getElementById(pageId);
    currentPage.classList.add('active');

    // Animation
    currentPage.style.opacity = '0';
    currentPage.style.transform = 'translateY(20px)';

    // Trigger reflow to start transition
    requestAnimationFrame(() => {
        currentPage.style.transition = 'opacity 0.3s ease, transform 0.5s ease';
        currentPage.style.opacity = '1';
        currentPage.style.transform = 'translateY(0)';
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Smooth scroll to contact
function scrollToContact() {
    showPage('home');
    setTimeout(() => {
        document.getElementById('contact-section').scrollIntoView({ behavior: 'smooth' });
    }, 500);
}

// Form submissions
async function submitInquiry(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('.submit-btn');
    const originalText = submitBtn.textContent;

    submitBtn.textContent = 'Sending...';
    submitBtn.disabled = true;
    submitBtn.style.opacity = '0.7';

    const formData = new FormData(event.target);
    const data = {
        name: formData.get('name'),
        phone: formData.get('phone'),
        email: formData.get('email'),
        note: formData.get('note')
    };

    try {
        const response = await fetch('/submit_inquiry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const result = await response.json();
        showSuccessMessage('Thank you for your inquiry! We will contact you soon.');

        form.querySelectorAll('input, textarea').forEach((input, index) => {
            setTimeout(() => {
                input.style.transform = 'scale(0.95)';
                input.style.opacity = '0.5';
                setTimeout(() => {
                    input.value = '';
                    input.style.transform = 'scale(1)';
                    input.style.opacity = '1';
                }, 150);
            }, index * 50);
        });
    } catch (error) {
        console.error('Error:', error);
        showSuccessMessage('Sorry, there was an error sending your message. Please try again.', 'error');
    } finally {
        setTimeout(() => {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
        }, 2000);
    }
}

async function submitRentalRequest(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('.submit-btn');
    const originalText = submitBtn.textContent;

    submitBtn.textContent = 'Processing...';
    submitBtn.disabled = true;
    submitBtn.style.opacity = '0.7';

    const formData = new FormData(form);
    const additionalNeeds = Array.from(form.querySelectorAll('input[name="additional_needs"]:checked')).map(cb => cb.value);

    const data = {
        name: formData.get('name'),
        phone: formData.get('phone'),
        email: formData.get('email'),
        event_type: formData.get('event_type'),
        space_requested: formData.get('space_requested'),
        event_date: formData.get('event_date'),
        start_time: formData.get('start_time'),
        end_time: formData.get('end_time'),
        guest_count: formData.get('guest_count'),
        additional_needs: additionalNeeds.join(', '),
        message: formData.get('message') || ''
    };

    try {
        const response = await fetch('/api/space-rental', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const result = await response.json();
        showSuccessMessage('Thank you for your rental request! We will contact you within 24-48 hours.');

        form.querySelectorAll('input, textarea, select').forEach((input, index) => {
            setTimeout(() => {
                input.style.transform = 'scale(0.95)';
                input.style.opacity = '0.5';
                setTimeout(() => {
                    if (input.type === 'checkbox') {
                        input.checked = false;
                    } else {
                        input.value = '';
                    }
                    input.style.transform = 'scale(1)';
                    input.style.opacity = '1';
                }, 150);
            }, index * 30);
        });
    } catch (error) {
        console.error('Error:', error);
        showSuccessMessage('Sorry, there was an error sending your request. Please try again.', 'error');
    } finally {
        setTimeout(() => {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
        }, 2000);
    }
}

// Success message
function showSuccessMessage(message, type = 'success') {
    const successDiv = document.getElementById('success-message');
    const messageText = successDiv.querySelector('p');
    const icon = successDiv.querySelector('i');
    const heading = successDiv.querySelector('h3');

    icon.className = type === 'error' ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle';
    icon.style.color = type === 'error' ? '#dc3545' : '#28a745';
    heading.textContent = type === 'error' ? 'Error' : 'Success!';
    messageText.textContent = message;

    successDiv.classList.add('show');

    setTimeout(() => successDiv.classList.remove('show'), 4000);
}

// Load events
async function loadEvents() {
    try {
        const response = await fetch('/api/events');
        if (!response.ok) throw new Error('Network response was not ok');
        const events = await response.json();
        displayEvents(events.slice(0, 3), 'home-events');
        displayEvents(events, 'all-events');
    } catch (error) {
        console.error('Error loading events:', error);
        showDefaultEvents();
    }
}

function displayEvents(events, containerId) {
    const container = document.getElementById(containerId);
    if (!events || events.length === 0) {
        showDefaultEvents();
        return;
    }

    container.innerHTML = events.map((event, index) => {
        const eventDate = new Date(event.event_date);
        const formattedDate = eventDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        const imageHtml = event.image_path
            ? `<img src="/static/${event.image_path}" alt="${event.title}" loading="lazy" style="animation-delay: ${index * 0.2}s">`
            : `<img src="{{ url_for('static', filename='images/event.jpg') }}" alt="${event.title}" loading="lazy" style="animation-delay: ${index * 0.2}s">`;

        return `
            <div class="event-card scale-in delay-${index + 1}" style="animation-delay: ${index * 0.2}s">
                ${imageHtml}
                <div class="event-content">
                    <div class="event-date">${formattedDate}</div>
                    <h3 class="event-title">${event.title}</h3>
                    <p>${event.description}</p>
                </div>
            </div>
        `;
    }).join('');

    setTimeout(() => {
        container.querySelectorAll('.scale-in').forEach(el => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                    }
                });
            }, { threshold: 0.1 });
            observer.observe(el);
        });
    }, 100);
}

function showDefaultEvents() {
    const defaultEvents = [
        {
            title: "Easter Celebration Service",
            description: "A joyous celebration of Christ's resurrection with special music, testimonies, and communion.",
            event_date: "2024-03-31",
            image_path: null
        },
        {
            title: "Community Outreach Program",
            description: "Serving our local community with food distribution and prayer ministry.",
            event_date: "2024-03-15",
            image_path: null
        },
        {
            title: "Youth Revival Conference",
            description: "A powerful weekend of worship, teaching, and fellowship for our young people.",
            event_date: "2024-02-28",
            image_path: null
        }
    ];

    displayEvents(defaultEvents.slice(0, 3), 'home-events');
    displayEvents(defaultEvents, 'all-events');
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    loadEvents();

    // Hamburger menu toggle
    const hamburger = document.querySelector('.hamburger');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    });

    // Close sidebar when a nav link is clicked
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    });

    // Hover effects
    document.querySelectorAll('.nav-links a').forEach(element => {
        element.addEventListener('mouseenter', () => element.style.transform += ' scale(1.05)');
        element.addEventListener('mouseleave', () => element.style.transform = element.style.transform.replace(' scale(1.05)', ''));
    });

    // Close sidebar when clicking overlay
    overlay.addEventListener('click', () => {
        hamburger.classList.remove('active');
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });

    document.querySelectorAll('.cta-button, .submit-btn, .nav-links a').forEach(element => {
        element.addEventListener('mouseenter', () => element.style.transform += ' scale(1.05)');
        element.addEventListener('mouseleave', () => element.style.transform = element.style.transform.replace(' scale(1.05)', ''));
    });

    // Parallax effect
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const hero = document.querySelector('.hero');
        if (hero) hero.style.transform = `translateY(${scrolled * -0.5}px)`;
    });

    // Initial animations
    setTimeout(() => {
        document.querySelectorAll('.fade-in').forEach((el, index) => {
            setTimeout(() => el.classList.add('visible'), index * 100);
        });
    }, 1000);
});