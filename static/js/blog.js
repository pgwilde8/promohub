// Blog-specific JavaScript functionality

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Reading progress indicator
    if (document.querySelector('article')) {
        const progressBar = createProgressBar();
        updateProgressBar(progressBar);
        
        window.addEventListener('scroll', () => updateProgressBar(progressBar));
    }
    
    // Social sharing buttons
    addSocialSharing();
});

function createProgressBar() {
    const progressBar = document.createElement('div');
    progressBar.id = 'reading-progress';
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background: linear-gradient(90deg, #007bff, #0056b3);
        z-index: 1000;
        transition: width 0.3s ease;
    `;
    document.body.appendChild(progressBar);
    return progressBar;
}

function updateProgressBar(progressBar) {
    const article = document.querySelector('article') || document.querySelector('main');
    if (!article) return;
    
    const rect = article.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const documentHeight = article.offsetHeight;
    
    const scrolled = Math.max(0, -rect.top);
    const progress = Math.min(100, (scrolled / (documentHeight - windowHeight)) * 100);
    
    progressBar.style.width = progress + '%';
}

function addSocialSharing() {
    const shareContainer = document.createElement('div');
    shareContainer.className = 'social-share mt-4 text-center';
    shareContainer.innerHTML = `
        <h6>Share this post:</h6>
        <div class="btn-group">
            <button class="btn btn-outline-primary btn-sm" onclick="shareOnTwitter()">
                <i class="fab fa-twitter me-1"></i>Twitter
            </button>
            <button class="btn btn-outline-primary btn-sm" onclick="shareOnLinkedIn()">
                <i class="fab fa-linkedin me-1"></i>LinkedIn
            </button>
            <button class="btn btn-outline-secondary btn-sm" onclick="copyShareLink()">
                <i class="fas fa-link me-1"></i>Copy Link
            </button>
        </div>
    `;
    
    const article = document.querySelector('article .card-body');
    if (article) {
        article.appendChild(shareContainer);
    }
}

function shareOnTwitter() {
    const title = document.title;
    const url = window.location.href;
    const text = `Check out this article: ${title}`;
    
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
}

function shareOnLinkedIn() {
    const url = window.location.href;
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`, '_blank');
}

function copyShareLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        alert('Link copied to clipboard!');
    });
}

// Newsletter signup (if implemented)
function subscribeNewsletter(email) {
    fetch('/api/leads', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: 'Blog Subscriber',
            email: email,
            source: 'blog_newsletter'
        })
    })
    .then(response => response.json())
    .then(data => {
        alert('Thanks for subscribing!');
    })
    .catch(error => {
        alert('Subscription failed. Please try again.');
    });
}