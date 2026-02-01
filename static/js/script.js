// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Form submission handler
document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="loading"></span> Predicting...';
    
    // Collect form data
    const formData = {
        applicant_income: parseFloat(document.getElementById('applicant_income').value),
        coapplicant_income: parseFloat(document.getElementById('coapplicant_income').value),
        age: parseFloat(document.getElementById('age').value),
        credit_score: parseFloat(document.getElementById('credit_score').value),
        loan_amount: parseFloat(document.getElementById('loan_amount').value),
        loan_term: parseFloat(document.getElementById('loan_term').value),
        dti_ratio: parseFloat(document.getElementById('dti_ratio').value),
        savings: parseFloat(document.getElementById('savings').value),
        collateral_value: parseFloat(document.getElementById('collateral_value').value),
        dependents: parseFloat(document.getElementById('dependents').value),
        existing_loans: parseFloat(document.getElementById('existing_loans').value),
        employment_status: document.getElementById('employment_status').value,
        marital_status: document.getElementById('marital_status').value,
        education_level: document.getElementById('education_level').value,
        gender: document.getElementById('gender').value,
        loan_purpose: document.getElementById('loan_purpose').value,
        property_area: document.getElementById('property_area').value,
        employer_category: document.getElementById('employer_category').value
    };
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayResult(result);
            // Scroll to result
            document.getElementById('result').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            alert('Error: ' + (result.error || 'Something went wrong'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error making prediction. Please try again.');
    } finally {
        // Reset button
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
    }
});

// Display prediction result
function displayResult(result) {
    const resultContainer = document.getElementById('result');
    const predictionText = document.getElementById('prediction-text');
    const approvedProgress = document.getElementById('approved-progress');
    const rejectedProgress = document.getElementById('rejected-progress');
    const approvedPercentage = document.getElementById('approved-percentage');
    const rejectedPercentage = document.getElementById('rejected-percentage');
    
    // Set prediction text
    if (result.prediction === 'Approved') {
        predictionText.textContent = '✅ Loan Approved!';
        predictionText.style.color = '#10b981';
    } else {
        predictionText.textContent = '❌ Loan Not Approved';
        predictionText.style.color = '#ef4444';
    }
    
    // Set progress bars
    approvedProgress.style.width = result.probability_approved + '%';
    rejectedProgress.style.width = result.probability_rejected + '%';
    
    // Set percentages
    approvedPercentage.textContent = result.probability_approved.toFixed(1) + '%';
    rejectedPercentage.textContent = result.probability_rejected.toFixed(1) + '%';
    
    // Show result container
    resultContainer.style.display = 'block';
}

// Reset form
function resetForm() {
    document.getElementById('predictionForm').reset();
    document.getElementById('result').style.display = 'none';
    
    // Reset progress bars
    document.getElementById('approved-progress').style.width = '0%';
    document.getElementById('rejected-progress').style.width = '0%';
}

// Add animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all cards and sections
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.feature-card, .metric-card, .stat-card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // Initialize dark mode
    initDarkMode();
});

// Dark Mode Functionality
function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const themeIcon = darkModeToggle.querySelector('.theme-icon');
    
    // Check for saved theme preference or default to light mode
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme, themeIcon);
    
    // Add click event listener
    darkModeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme, themeIcon);
    });
}

function updateThemeIcon(theme, iconElement) {
    if (theme === 'dark') {
        iconElement.textContent = '☀️';
    } else {
        iconElement.textContent = '🌙';
    }
}
