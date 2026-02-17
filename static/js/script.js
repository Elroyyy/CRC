// // Preloader
// window.addEventListener('load', () => {
//     const preloader = document.getElementById('preloader');
//     const progressFill = document.getElementById('progress-fill');
//
//     let progress = 0;
//     const interval = setInterval(() => {
//         progress += Math.random() * 30;
//         if (progress >= 100) {
//             progress = 100;
//             clearInterval(interval);
//             setTimeout(() => {
//                 preloader.classList.add('hidden');
//                 initializeAnimations();
//             }, 500);
//         }
//         progressFill.style.width = `${progress}%`;
//     }, 100);
//
//     // Fallback: Hide preloader after 5 seconds
//     setTimeout(hidePreloader, 5000);
//
//     function hidePreloader() {
//         clearInterval(interval);
//         preloader.classList.add('hidden');
//         console.log('Preloader hidden');
//         initializeAnimations();
//         // Ensure home page is visible
//         const homePage = document.getElementById('home');
//         if (homePage) {
//             homePage.classList.add('active');
//             homePage.style.opacity = '1';
//             homePage.style.transform = 'translateY(0)';
//         }
//     }
// });

window.addEventListener('load', () => {
    // Start animations directly
    initializeAnimations();

    // Ensure home page is visible
    const homePage = document.getElementById('home');
    if (homePage) {
        homePage.classList.add('active');
        homePage.style.opacity = '1';
        homePage.style.transform = 'translateY(0)';
    }
});


// // Create floating particles (optimized for performance)
// function createParticles() {
//     const particlesContainer = document.getElementById('particles');
//     const particleCount = window.innerWidth < 768 ? 20 : 50; // Reduce particles on mobile
//     for (let i = 0; i < particleCount; i++) {
//         const particle = document.createElement('div');
//         particle.className = 'particle';
//         particle.style.left = `${Math.random() * 100}%`;
//         particle.style.width = particle.style.height = `${Math.random() * 4 + 2}px`;
//         particle.style.animationDelay = `${Math.random() * 8}s`;
//         particle.style.animationDuration = `${Math.random() * 4 + 4}s`;
//         particlesContainer.appendChild(particle);
//     }
// }

// Initialize animations
function initializeAnimations() {
    // createParticles();
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
function showPage(pageId, updateURL = true) {

    // Update URL without #
    if (updateURL) {
        history.pushState({ page: pageId }, '', '/' + pageId);
    }

    const pages = document.querySelectorAll('.page');

    pages.forEach(page => {
        page.classList.remove('active');
        page.style.display = 'none';
    });

    const currentPage = document.getElementById(pageId);
    if (!currentPage) return;

    currentPage.classList.add('active');
    currentPage.style.display = 'block';

    // Animation
    currentPage.style.opacity = '0';
    currentPage.style.transform = 'translateY(20px)';

    requestAnimationFrame(() => {
        currentPage.style.transition = 'opacity 0.3s ease, transform 0.5s ease';
        currentPage.style.opacity = '1';
        currentPage.style.transform = 'translateY(0)';
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
    return false;
}


// Handle browser back/forward buttons
window.addEventListener('popstate', function (event) {

    const pageId = event.state?.page || 'home';
    showPage(pageId, false);

});


// Handle initial page load
document.addEventListener('DOMContentLoaded', function () {

    // Get page name from URL path
    let path = window.location.pathname.replace('/', '');

    if (path === '') {
        path = 'home';
    }

    showPage(path, false);

});


// Smooth scroll to contact
function scrollToContact() {
    showPage('home');
    setTimeout(() => {
        document.getElementById('contact-section').scrollIntoView({ behavior: 'smooth' });
    }, 500);

    return false;
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

// Sermon Data and Functions
const sermonData = {
    'sample1': {
        title: "True Fasting",
        date: "December 29, 2016",
        preacher: "Pastor Niranjan",
        description: "As a church we sought the face of the Lord in fasting for a week.. But it was good for God to speak to us through Pastor Niranjan.. He reminded us of the true meaning of fasting...",
        youtubeId: "CaTb2JoALNw", // Replace with actual YouTube video ID
        audioFile: null, // Or null if no file
        audioLink: null // Or null if no link
    },
    'sample2': {
        title: "God is in the boat",
        date: "August 13, 2016",
        preacher: "Pastor Robert Gallagher",
        description: "A biblical exegesis of Mark 4: 35-41 .. The story exists to remind us that God is in the boat with us, and all we need to do is have some faith that he would take us to the other side as he promised!!! Watch, listen and be blessed!",
        youtubeId: "kziS51dikY0", // Replace with actual YouTube video ID
        audioFile: null,
        audioLink: null
    },
    'sample3': {
        title: "Sermon Excerpt - Truth Lovers",
        date: "July 10, 2026",
        preacher: "Pastor Nathanael Somanathan",
        description: "Seeking for a reformation within tamil christian circles, with a resurgence of Gospel centred truth and sound doctrine!!",
        youtubeId: "CyMZ_CJ4Vjo", // No video
        audioFile: null,
        audioLink: null
    }
};

function openSermon(sermonKey) {
    const sermon = sermonData[sermonKey];
    if (!sermon) return;

    const modal = document.getElementById('sermonModal');

    // Set title and metadata
    document.getElementById('sermonTitle').textContent = sermon.title;
    document.getElementById('sermonDate').innerHTML = `<i class="fas fa-calendar"></i> ${sermon.date}`;
    document.getElementById('sermonPreacher').innerHTML = `<i class="fas fa-user"></i> ${sermon.preacher}`;
    document.getElementById('sermonDescription').textContent = sermon.description;

    // Clear previous content
    document.getElementById('sermonVideoContainer').innerHTML = '';
    document.getElementById('sermonAudioContainer').innerHTML = '';

    // Add YouTube video if available
    if (sermon.youtubeId) {
        const videoHTML = `
            <div class="video-container">
                <iframe 
                    src="https://www.youtube.com/embed/${sermon.youtubeId}?autoplay=1" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
        `;
        document.getElementById('sermonVideoContainer').innerHTML = videoHTML;
    }

    // Add audio player if available
    if (sermon.audioFile || sermon.audioLink) {
        let audioHTML = '<div class="audio-player">';
        audioHTML += '<h3><i class="fas fa-headphones"></i> Listen to Audio</h3>';

        // Add audio player if file is available
        if (sermon.audioFile) {
            audioHTML += `
                <audio controls>
                    <source src="${sermon.audioFile}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            `;
        }

        // Add download/external links
        audioHTML += '<div class="audio-links">';

        if (sermon.audioFile) {
            audioHTML += `
                <a href="${sermon.audioFile}" download class="audio-link">
                    <i class="fas fa-download"></i> Download Audio
                </a>
            `;
        }

        if (sermon.audioLink) {
            audioHTML += `
                <a href="${sermon.audioLink}" target="_blank" class="audio-link">
                    <i class="fab fa-google-drive"></i> Listen on Google Drive
                </a>
            `;
        }

        audioHTML += '</div></div>';
        document.getElementById('sermonAudioContainer').innerHTML = audioHTML;
    }

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeSermon() {
    const modal = document.getElementById('sermonModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';

    // Stop video playback
    const videoContainer = document.getElementById('sermonVideoContainer');
    videoContainer.innerHTML = '';
}

// Close sermon modal when clicking outside
document.getElementById('sermonModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeSermon();
    }
});

// Load sermons from API
function loadSermons() {
    fetch('/api/sermons')
        .then(response => response.json())
        .then(sermons => {
            if (sermons && sermons.length > 0) {
                displaySermons(sermons);
            }
        })
        .catch(error => {
            console.error('Error loading sermons:', error);
            // Keep default sample sermons if API fails
        });
}

function displaySermons(sermons) {
    const container = document.getElementById('sermons-container');

    const sermonsHTML = sermons.map((sermon, index) => {
        const badges = [];
        if (sermon.video_link || sermon.video_path) {
            badges.push('<span class="sermon-badge"><i class="fas fa-video"></i> Video</span>');
        }
        if (sermon.audio_link || sermon.audio_path) {
            badges.push('<span class="sermon-badge"><i class="fas fa-headphones"></i> Audio</span>');
        }

        return `
            <div class="sermon-card scale-in delay-${index % 3}" onclick="openSermonFromAPI(${sermon.id})">
                <div class="sermon-image">
                    <img src="${sermon.image_path ? '/static/' + sermon.image_path : '/static/images/event.jpg'}" alt="${sermon.title}">
                    <div class="sermon-play-overlay">
                        <i class="fas fa-play"></i>
                    </div>
                </div>
                <div class="sermon-content">
                    <div class="sermon-meta">
                        <span class="sermon-date">
                            <i class="fas fa-calendar"></i> ${new Date(sermon.sermon_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </span>
                        <span class="sermon-preacher">
                            <i class="fas fa-user"></i> ${sermon.preacher || 'Pastor'}
                        </span>
                    </div>
                    <h3 class="sermon-title">${sermon.title}</h3>
                    <p class="sermon-description">${sermon.description.substring(0, 100)}...</p>
                    <div class="sermon-badges">
                        ${badges.join('')}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = sermonsHTML;
}

function openSermonFromAPI(sermonId) {
    fetch(`/api/sermons/${sermonId}`)
        .then(response => response.json())
        .then(sermon => {
            // Convert API sermon to modal format
            const modal = document.getElementById('sermonModal');

            document.getElementById('sermonTitle').textContent = sermon.title;
            document.getElementById('sermonDate').innerHTML = `<i class="fas fa-calendar"></i> ${new Date(sermon.sermon_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`;
            document.getElementById('sermonPreacher').innerHTML = `<i class="fas fa-user"></i> ${sermon.preacher || 'Pastor'}`;
            document.getElementById('sermonDescription').textContent = sermon.description;

            document.getElementById('sermonVideoContainer').innerHTML = '';
            document.getElementById('sermonAudioContainer').innerHTML = '';

            // Handle video (YouTube link or file)
            if (sermon.video_link) {
                const youtubeId = extractYouTubeID(sermon.video_link);
                if (youtubeId) {
                    document.getElementById('sermonVideoContainer').innerHTML = `
                        <div class="video-container">
                            <iframe 
                                src="https://www.youtube.com/embed/${youtubeId}?autoplay=1" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowfullscreen>
                            </iframe>
                        </div>
                    `;
                }
            } else if (sermon.video_path) {
                document.getElementById('sermonVideoContainer').innerHTML = `
                    <div class="video-container">
                        <video controls autoplay style="width: 100%; height: 100%; object-fit: contain;">
                            <source src="/static/${sermon.video_path}" type="video/mp4">
                            Your browser does not support the video element.
                        </video>
                    </div>
                `;
            }

            // Handle audio
            if (sermon.audio_path || sermon.audio_link) {
                let audioHTML = '<div class="audio-player">';
                audioHTML += '<h3><i class="fas fa-headphones"></i> Listen to Audio</h3>';

                if (sermon.audio_path) {
                    audioHTML += `
                        <audio controls>
                            <source src="/static/${sermon.audio_path}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    `;
                }

                audioHTML += '<div class="audio-links">';

                if (sermon.audio_path) {
                    audioHTML += `
                        <a href="/static/${sermon.audio_path}" download class="audio-link">
                            <i class="fas fa-download"></i> Download Audio
                        </a>
                    `;
                }

                if (sermon.audio_link) {
                    audioHTML += `
                        <a href="${sermon.audio_link}" target="_blank" class="audio-link">
                            <i class="fab fa-google-drive"></i> Listen on Google Drive
                        </a>
                    `;
                }

                audioHTML += '</div></div>';
                document.getElementById('sermonAudioContainer').innerHTML = audioHTML;
            }

            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        })
        .catch(error => {
            console.error('Error loading sermon:', error);
            alert('Error loading sermon. Please try again.');
        });
}

function extractYouTubeID(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
}

// Load sermons when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Uncomment when API is ready
    // loadSermons();
});

