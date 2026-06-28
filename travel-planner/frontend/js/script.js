/**
 * AI Travel Planner — Frontend JavaScript
 * Handles form submission, API calls, loading states, and result rendering.
 */

const API_BASE_URL = 'http://localhost:8000';

// --- DOM References ---
const tripForm = document.getElementById('trip-form');
const submitBtn = document.getElementById('submit-btn');
const formSection = document.getElementById('form-section');
const loadingSection = document.getElementById('loading-section');
const errorSection = document.getElementById('error-section');
const resultsSection = document.getElementById('results-section');
const errorMessage = document.getElementById('error-message');

// --- Set minimum dates to today ---
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('startDate').setAttribute('min', today);
    document.getElementById('endDate').setAttribute('min', today);

    document.getElementById('startDate').addEventListener('change', (e) => {
        document.getElementById('endDate').setAttribute('min', e.target.value);
    });
});

// --- Form Submission ---
tripForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = collectFormData();
    const errors = validateFormData(formData);

    if (errors.length > 0) {
        showError(errors.join('\n'));
        return;
    }

    await handleFormSubmit(formData);
});

/**
 * Collect all form values into a request payload.
 */
function collectFormData() {
    const preferences = [];
    document.querySelectorAll('input[name="preferences"]:checked').forEach((cb) => {
        preferences.push(cb.value);
    });

    return {
        destination: document.getElementById('destination').value,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        budget: parseFloat(document.getElementById('budget').value),
        travelers: parseInt(document.getElementById('travelers').value) || 1,
        preferences: preferences.length > 0 ? preferences : ['Historical', 'Budget'],
        accommodation_preference: document.getElementById('accommodation').value,
    };
}

/**
 * Validate form data before submission.
 */
function validateFormData(data) {
    const errors = [];

    if (!data.destination) errors.push('Please select a destination');
    if (!data.start_date) errors.push('Please select a start date');
    if (!data.end_date) errors.push('Please select an end date');
    if (!data.budget || data.budget <= 0) errors.push('Please enter a valid budget');
    if (data.budget < 1000) errors.push('Minimum budget is ₹1,000');
    if (data.budget > 500000) errors.push('Maximum budget is ₹5,00,000');

    if (data.start_date && data.end_date) {
        const start = new Date(data.start_date);
        const end = new Date(data.end_date);
        if (end <= start) errors.push('End date must be after start date');

        const diffDays = (end - start) / (1000 * 60 * 60 * 24);
        if (diffDays > 14) errors.push('Trip duration cannot exceed 14 days');
    }

    return errors;
}

/**
 * Main form submission handler.
 */
async function handleFormSubmit(formData) {
    showLoadingState();

    try {
        const response = await callGenerateItineraryAPI(formData);

        if (response.success) {
            renderItinerary(response);
        } else {
            showError(response.detail || 'Failed to generate itinerary');
        }
    } catch (error) {
        console.error('API Error:', error);
        showError(error.message || 'Unable to connect to the server. Make sure the backend is running on port 8000.');
    }
}

/**
 * Call the backend API to generate an itinerary.
 */
async function callGenerateItineraryAPI(formData) {
    const response = await fetch(`${API_BASE_URL}/api/generate-itinerary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    return await response.json();
}

// --- State Management ---

function hideAllStates() {
    formSection.style.display = 'none';
    loadingSection.style.display = 'none';
    errorSection.style.display = 'none';
    resultsSection.style.display = 'none';
}

function showLoadingState() {
    hideAllStates();
    loadingSection.style.display = 'block';
    animateLoadingSteps();
}

function showError(message) {
    hideAllStates();
    formSection.style.display = 'block';
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
    window.scrollTo({ top: errorSection.offsetTop - 20, behavior: 'smooth' });
}

function resetForm() {
    hideAllStates();
    formSection.style.display = 'block';
    submitBtn.querySelector('.btn-text').style.display = 'inline';
    submitBtn.querySelector('.btn-loader').style.display = 'none';
    submitBtn.disabled = false;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Animate loading step indicators progressively.
 */
function animateLoadingSteps() {
    const steps = document.querySelectorAll('.loading-step');
    let currentStep = 0;

    // Reset all steps
    steps.forEach((s) => { s.classList.remove('active', 'done'); });
    steps[0].classList.add('active');

    const interval = setInterval(() => {
        if (currentStep < steps.length - 1) {
            steps[currentStep].classList.remove('active');
            steps[currentStep].classList.add('done');
            steps[currentStep].querySelector('.step-icon').textContent = '✅';
            currentStep++;
            steps[currentStep].classList.add('active');
        } else {
            clearInterval(interval);
        }
    }, 3000);

    // Store interval for cleanup
    window._loadingInterval = interval;
}

// --- Rendering ---

/**
 * Render the full itinerary response into the DOM.
 */
function renderItinerary(response) {
    if (window._loadingInterval) clearInterval(window._loadingInterval);

    hideAllStates();
    resultsSection.style.display = 'block';

    const data = response.data;
    const summary = response.summary;

    // Title
    document.getElementById('results-title').textContent =
        `Your ${summary.destination} Itinerary`;

    // Summary Cards
    renderSummaryCards(summary, data);

    // Hotel
    renderHotel(summary, data);

    // Daily Plans
    renderDailyPlans(data.daily_plans || []);

    // Budget Breakdown
    renderBudgetBreakdown(data.budget_summary || {}, summary.total_budget);

    // Hidden Gems
    renderHiddenGems(data.hidden_gems || []);

    // Travel Tips
    renderTravelTips(data.travel_tips || []);

    // Emergency Contacts
    renderEmergencyContacts(data.emergency_contacts || {});

    window.scrollTo({ top: resultsSection.offsetTop - 20, behavior: 'smooth' });
}

function renderSummaryCards(summary, data) {
    const grid = document.getElementById('summary-grid');
    const estimated = data.budget_summary?.total_estimated || summary.total_estimated_cost || summary.total_budget;

    grid.innerHTML = `
        <div class="summary-card">
            <span class="card-icon">💰</span>
            <div class="card-value">₹${formatNumber(summary.total_budget)}</div>
            <div class="card-label">Budget</div>
        </div>
        <div class="summary-card">
            <span class="card-icon">📊</span>
            <div class="card-value">₹${formatNumber(estimated)}</div>
            <div class="card-label">Est. Cost</div>
        </div>
        <div class="summary-card">
            <span class="card-icon">📅</span>
            <div class="card-value">${summary.duration_days} Days</div>
            <div class="card-label">Duration</div>
        </div>
        <div class="summary-card">
            <span class="card-icon">💵</span>
            <div class="card-value">₹${formatNumber(Math.round(summary.total_budget / summary.duration_days))}</div>
            <div class="card-label">Per Day</div>
        </div>
    `;
}

function renderHotel(summary, data) {
    const container = document.getElementById('hotel-details');
    // Handle both `hotels` (fallback) and `hotels_summary` (LLM) keys
    const hotelsList = data.hotels || data.hotels_summary || [];
    const hotel = (hotelsList.length > 0 && hotelsList[0]) || {};
    const name = hotel.name || summary.hotel_recommended || 'Recommended Hotel';
    const price = hotel.price_per_night || summary.hotel_cost_per_night || 0;
    const rating = hotel.rating || '';
    const location = hotel.location || '';
    const amenities = hotel.amenities || [];

    let amenitiesHTML = amenities.map(a => `<span class="amenity-tag">${a}</span>`).join('');

    container.innerHTML = `
        <div class="hotel-info">
            <div>
                <div class="hotel-name">${name}</div>
                ${location ? `<div class="hotel-location">📍 ${location}</div>` : ''}
                ${rating ? `<div class="hotel-rating">⭐ ${rating}/5</div>` : ''}
            </div>
            <div>
                <div class="hotel-price">₹${formatNumber(price)}</div>
                <div class="hotel-price-label">per night</div>
            </div>
        </div>
        ${amenitiesHTML ? `<div class="hotel-amenities">${amenitiesHTML}</div>` : ''}
    `;
}

function renderDailyPlans(dailyPlans) {
    const container = document.getElementById('daily-plans');
    container.innerHTML = '';

    dailyPlans.forEach((day, index) => {
        const dayCard = document.createElement('div');
        dayCard.className = 'day-card';
        dayCard.style.animationDelay = `${0.1 * (index + 1)}s`;

        const morning = day.morning || {};
        const afternoon = day.afternoon || {};
        const evening = day.evening || {};

        dayCard.innerHTML = `
            <div class="day-header" onclick="this.parentElement.querySelector('.day-body').classList.toggle('collapsed')">
                <div class="day-info">
                    <div class="day-number">${day.day}</div>
                    <div>
                        <div class="day-title">${day.theme || `Day ${day.day} Adventure`}</div>
                        <div class="day-date">${formatDate(day.date)}</div>
                    </div>
                </div>
                <div class="day-cost">₹${formatNumber(day.day_total || 0)}</div>
            </div>
            <div class="day-body">
                ${renderTimeSlot('morning', 'Morning', morning)}
                ${renderTimeSlot('afternoon', 'Afternoon', afternoon)}
                ${renderTimeSlot('evening', 'Evening', evening)}
            </div>
        `;

        container.appendChild(dayCard);
    });
}

function renderTimeSlot(period, label, slot) {
    if (!slot) return '';

    // Handle both schemas: `activity` (string) or `activities` (array)
    let activity = '';
    if (slot.activity) {
        activity = slot.activity;
    } else if (slot.activities && Array.isArray(slot.activities)) {
        activity = slot.activities.join(' → ');
    } else if (slot.name) {
        activity = slot.name;
    } else {
        return '';
    }

    const time = slot.time || slot.timing || '';
    const cost = slot.cost || slot.estimated_cost || 0;
    const description = slot.description || '';

    return `
        <div class="time-slot">
            <div class="slot-time-badge">
                <span class="slot-period ${period}">${label}</span>
                ${time ? `<span class="slot-time">${time}</span>` : ''}
            </div>
            <div class="slot-details">
                <div class="slot-activity">${activity}</div>
                ${description ? `<div class="slot-description">${description}</div>` : ''}
                <span class="slot-cost">₹${formatNumber(cost)}</span>
            </div>
        </div>
    `;
}

function renderBudgetBreakdown(budgetSummary, totalBudget) {
    const container = document.getElementById('budget-breakdown');

    const items = [
        { icon: '🏨', label: 'Accommodation', value: budgetSummary.accommodation_total || 0 },
        { icon: '🍽️', label: 'Food & Dining', value: budgetSummary.food_total || 0 },
        { icon: '🎯', label: 'Activities', value: budgetSummary.activities_total || 0 },
        { icon: '🚗', label: 'Transport', value: budgetSummary.transport_total || 0 },
        { icon: '📦', label: 'Miscellaneous', value: budgetSummary.miscellaneous || 0 },
    ];

    const total = budgetSummary.total_estimated || items.reduce((s, i) => s + i.value, 0);
    const percentage = totalBudget > 0 ? Math.round((total / totalBudget) * 100) : 100;
    const isOver = percentage > 100;

    let html = items
        .map(
            (item) => `
        <div class="budget-item">
            <span class="budget-label">${item.icon} ${item.label}</span>
            <span class="budget-value">₹${formatNumber(item.value)}</span>
        </div>
    `
        )
        .join('');

    html += `
        <div class="budget-item total">
            <span class="budget-label">Total Estimated</span>
            <span class="budget-value">₹${formatNumber(total)}</span>
        </div>
        <div class="budget-bar-container">
            <div class="budget-bar-label">
                <span>₹0</span>
                <span>${percentage}% of budget</span>
                <span>₹${formatNumber(totalBudget)}</span>
            </div>
            <div class="budget-bar">
                <div class="budget-bar-fill ${isOver ? 'over' : 'under'}"
                     style="width: ${Math.min(percentage, 100)}%"></div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

function renderHiddenGems(gems) {
    const container = document.getElementById('hidden-gems');

    if (!gems || gems.length === 0) {
        document.getElementById('gems-card').style.display = 'none';
        return;
    }

    container.innerHTML = gems
        .map(
            (gem) => `
        <div class="gem-item">
            <span class="gem-icon">💎</span>
            <div>
                <div class="gem-name">${gem.name}</div>
                <div class="gem-description">${gem.description}</div>
                ${gem.cost !== undefined ? `<div class="gem-cost">${gem.cost === 0 ? 'Free entry' : `₹${formatNumber(gem.cost)}`}</div>` : ''}
            </div>
        </div>
    `
        )
        .join('');
}

function renderTravelTips(tips) {
    const container = document.getElementById('travel-tips');

    if (!tips || tips.length === 0) {
        document.getElementById('tips-card').style.display = 'none';
        return;
    }

    container.innerHTML = tips.map((tip) => `<li>${tip}</li>`).join('');
}

function renderEmergencyContacts(contacts) {
    const container = document.getElementById('emergency-contacts');

    if (!contacts || Object.keys(contacts).length === 0) {
        document.getElementById('emergency-card').style.display = 'none';
        return;
    }

    const friendlyNames = {
        police: '🚔 Police',
        ambulance: '🚑 Ambulance',
        tourist_helpline: '📞 Tourist Helpline',
        women_helpline: '👩 Women Helpline',
        fire: '🚒 Fire',
        local_hospital: '🏥 Hospital',
    };

    container.innerHTML = `<div class="emergency-grid">
        ${Object.entries(contacts)
            .map(
                ([key, value]) => `
            <div class="emergency-item">
                <div>
                    <div class="emergency-label">${friendlyNames[key] || key}</div>
                    <div class="emergency-number">${value}</div>
                </div>
            </div>
        `
            )
            .join('')}
    </div>`;
}

// --- Utility Functions ---

function formatNumber(num) {
    if (num === undefined || num === null) return '0';
    return Math.round(num).toLocaleString('en-IN');
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr + 'T00:00:00');
        return date.toLocaleDateString('en-IN', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            year: 'numeric',
        });
    } catch {
        return dateStr;
    }
}
