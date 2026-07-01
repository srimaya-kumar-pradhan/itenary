/**
 * AI Travel Planner — Frontend JavaScript
 * Enhanced with hotel comparison, meal planning, transport info,
 * and interactive map with route visualization.
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

    // Hotel with comparison
    renderHotel(summary, data, response.hotel_comparison);

    // Daily Plans (enhanced with meals & transport)
    renderDailyPlans(data.daily_plans || []);

    // Budget Breakdown (enhanced with detailed allocation)
    renderBudgetBreakdown(data.budget_summary || {}, summary.total_budget, response.budget_detailed);

    // Transport Summary
    renderTransportSummary(response.transport_summary);

    // Hidden Gems
    renderHiddenGems(data.hidden_gems || []);

    // Travel Tips
    renderTravelTips(data.travel_tips || []);

    // Emergency Contacts
    renderEmergencyContacts(data.emergency_contacts || {});

    // Validation Warnings
    renderValidationWarnings(response.validation_warnings || []);

    // Initialize Map and setup responsive mobile triggers
    initOrUpdateMap(data, summary.destination);
    setupMobileToggles();

    window.scrollTo({ top: resultsSection.offsetTop - 20, behavior: 'smooth' });
}

function renderSummaryCards(summary, data) {
    const grid = document.getElementById('summary-grid');
    const estimated = data.budget_summary?.total_estimated || summary.total_estimated_cost || summary.total_budget;
    const budgetStatus = estimated <= summary.total_budget ? '✅' : '⚠️';

    grid.innerHTML = `
        <div class="summary-card">
            <span class="card-icon">💰</span>
            <div class="card-value">₹${formatNumber(summary.total_budget)}</div>
            <div class="card-label">Budget</div>
        </div>
        <div class="summary-card">
            <span class="card-icon">📊</span>
            <div class="card-value">₹${formatNumber(estimated)} ${budgetStatus}</div>
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

function renderHotel(summary, data, hotelComparison) {
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

    // Hotel comparison section
    let comparisonHTML = '';
    if (hotelComparison && hotelComparison.length > 0) {
        comparisonHTML = `
            <div class="hotel-comparison-section">
                <h4 class="comparison-title">🔍 Price Comparison Across Platforms</h4>
                <div class="comparison-grid">
                    ${hotelComparison.slice(0, 3).map(h => {
                        const comparisons = h.price_comparisons || [];
                        const platformCards = comparisons.map(pc => `
                            <div class="platform-price ${pc.platform === h.best_platform ? 'best-deal' : ''}">
                                <div class="platform-name">${getPlatformIcon(pc.platform)} ${pc.platform.charAt(0).toUpperCase() + pc.platform.slice(1)}</div>
                                <div class="platform-price-value">₹${formatNumber(pc.price_per_night)}<span>/night</span></div>
                                ${pc.platform === h.best_platform ? '<div class="best-badge">Best Deal</div>' : ''}
                            </div>
                        `).join('');

                        return `
                            <div class="comparison-card">
                                <div class="comparison-hotel-header">
                                    <div class="comparison-hotel-name">${h.name}</div>
                                    <div class="comparison-hotel-meta">
                                        ⭐ ${h.rating || 'N/A'} · 📍 ${h.location || 'N/A'}
                                        ${h.savings > 0 ? `<span class="savings-badge">Save ₹${formatNumber(h.savings)} (${h.savings_percentage}%)</span>` : ''}
                                    </div>
                                </div>
                                <div class="platform-prices">${platformCards}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

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
        ${comparisonHTML}
    `;
}

function getPlatformIcon(platform) {
    const icons = {
        booking: '🅱️',
        agoda: '🅰️',
        makemytrip: '✈️',
    };
    return icons[platform] || '🏨';
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
        const meals = day.meals || [];
        const transport = day.transport || [];
        const warnings = day.warnings || [];

        // Build cost breakdown line
        let costBreakdown = '';
        if (day.activities_cost !== undefined) {
            costBreakdown = `
                <div class="day-cost-breakdown">
                    <span title="Activities">🎯 ₹${formatNumber(day.activities_cost || 0)}</span>
                    <span title="Meals">🍽️ ₹${formatNumber(day.meals_cost || 0)}</span>
                    <span title="Transport">🚗 ₹${formatNumber(day.transport_cost || 0)}</span>
                    <span title="Hotel">🏨 ₹${formatNumber(day.hotel_cost || 0)}</span>
                </div>
            `;
        }

        // Build meals section
        let mealsHTML = '';
        if (meals.length > 0) {
            mealsHTML = `
                <div class="meals-section">
                    <div class="meals-title">🍽️ Meals</div>
                    <div class="meals-grid">
                        ${meals.map(m => `
                            <div class="meal-item meal-${m.type}">
                                <span class="meal-type">${getMealIcon(m.type)} ${m.type.charAt(0).toUpperCase() + m.type.slice(1)}</span>
                                <span class="meal-restaurant">${m.restaurant || 'Local restaurant'}</span>
                                <span class="meal-cuisine">${m.cuisine || ''}</span>
                                <span class="meal-cost">₹${formatNumber(m.estimated_cost || 0)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Build transport section
        let transportHTML = '';
        if (transport.length > 0) {
            transportHTML = `
                <div class="transport-section">
                    <div class="transport-title">🚌 Getting Around</div>
                    <div class="transport-legs">
                        ${transport.map(t => `
                            <div class="transport-leg">
                                <span class="transport-route">${t.from || '📍'} → ${t.to || '📍'}</span>
                                <span class="transport-mode">${getTransportIcon(t.mode)} ${(t.mode || 'auto').charAt(0).toUpperCase() + (t.mode || 'auto').slice(1)}</span>
                                <span class="transport-details">₹${formatNumber(t.cost || 0)} · ${t.time_minutes || '~20'}min</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Build warnings section
        let warningsHTML = '';
        if (warnings.length > 0) {
            warningsHTML = `
                <div class="day-warnings">
                    ${warnings.map(w => `<div class="warning-item">⚠️ ${w}</div>`).join('')}
                </div>
            `;
        }

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
                ${costBreakdown}
                ${warningsHTML}
                ${renderTimeSlot('morning', 'Morning', morning)}
                ${renderTimeSlot('afternoon', 'Afternoon', afternoon)}
                ${renderTimeSlot('evening', 'Evening', evening)}
                ${mealsHTML}
                ${transportHTML}
            </div>
        `;

        container.appendChild(dayCard);
    });
}

function getMealIcon(type) {
    const icons = { breakfast: '🥐', lunch: '🍛', dinner: '🍽️', snacks: '🍿' };
    return icons[type] || '🍴';
}

function getTransportIcon(mode) {
    const icons = { metro: '🚇', auto: '🛺', taxi: '🚕', bus: '🚌', walking: '🚶' };
    return icons[mode] || '🚗';
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

    // Extract coordinate attributes if available
    const latAttr = (slot.coordinates && slot.coordinates.lat) ? `data-lat="${slot.coordinates.lat}"` : '';
    const lngAttr = (slot.coordinates && slot.coordinates.lng) ? `data-lng="${slot.coordinates.lng}"` : '';

    return `
        <div class="time-slot" ${latAttr} ${lngAttr}>
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

function renderBudgetBreakdown(budgetSummary, totalBudget, budgetDetailed) {
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

    // Add meal breakdown if available
    if (budgetDetailed && budgetDetailed.meals) {
        const meals = budgetDetailed.meals;
        html += `
            <div class="budget-meal-breakdown">
                <div class="budget-item sub-item">
                    <span class="budget-label">  🥐 Breakfast/day</span>
                    <span class="budget-value">₹${formatNumber(meals.breakfast || 0)}</span>
                </div>
                <div class="budget-item sub-item">
                    <span class="budget-label">  🍛 Lunch/day</span>
                    <span class="budget-value">₹${formatNumber(meals.lunch || 0)}</span>
                </div>
                <div class="budget-item sub-item">
                    <span class="budget-label">  🍽️ Dinner/day</span>
                    <span class="budget-value">₹${formatNumber(meals.dinner || 0)}</span>
                </div>
            </div>
        `;
    }

    // Budget warnings
    if (budgetDetailed && budgetDetailed.warnings && budgetDetailed.warnings.length > 0) {
        html += `
            <div class="budget-warnings">
                ${budgetDetailed.warnings.map(w => `<div class="budget-warning-item">⚠️ ${w}</div>`).join('')}
            </div>
        `;
    }

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

function renderTransportSummary(transportSummary) {
    const container = document.getElementById('transport-summary');
    if (!container) return;

    if (!transportSummary) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    let html = '';

    if (transportSummary.has_metro && transportSummary.metro_info) {
        const metro = transportSummary.metro_info;
        html += `
            <div class="metro-info-card">
                <div class="metro-header">
                    <span class="metro-icon">🚇</span>
                    <span class="metro-name">${metro.name}</span>
                </div>
                <div class="metro-details">
                    <span>🕐 ${metro.hours}</span>
                    <span>🎫 Day Pass: ₹${metro.day_pass}</span>
                    <span>📱 ${metro.app}</span>
                </div>
                <div class="metro-stations">
                    <div class="stations-title">Key Tourist Stations:</div>
                    ${metro.key_tourist_stations.slice(0, 4).map(s => 
                        `<div class="station-item">🚉 ${s}</div>`
                    ).join('')}
                </div>
            </div>
        `;
    }

    if (transportSummary.daily_estimate) {
        const est = transportSummary.daily_estimate;
        html += `
            <div class="transport-estimate">
                <span>Daily transport estimate: <strong>₹${formatNumber(est.total_daily_cost)}</strong></span>
                <span>Recommended mode: <strong>${getTransportIcon(est.recommended_mode)} ${est.recommended_mode}</strong></span>
            </div>
        `;
    }

    container.innerHTML = html;
}

function renderValidationWarnings(warnings) {
    const container = document.getElementById('validation-warnings');
    if (!container) return;

    if (!warnings || warnings.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    container.innerHTML = `
        <div class="validation-warnings-list">
            ${warnings.map(w => `<div class="validation-warning-item">⚠️ ${w}</div>`).join('')}
        </div>
    `;
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

// ==============================================================
// INTERACTIVE GEOMETRIC MAP INTEGRATION (LEAFLET ENGINE)
// ==============================================================

let itineraryMap = null;
let mapMarkers = [];
let mapRouteLine = null;
let mapTileLayer = null;

/**
 * Wait for loading screen astronaut to fade/dismiss before initializing map
 */
async function initOrUpdateMap(data, destination) {
    const loader = document.getElementById('global-loader');
    
    // Safety check: wait for loader display: none or opacity: 0
    const isLoaderDismissed = () => {
        if (!loader) return true;
        const style = window.getComputedStyle(loader);
        return style.display === 'none' || style.opacity === '0';
    };

    if (!isLoaderDismissed()) {
        await new Promise(resolve => {
            const checkInterval = setInterval(() => {
                if (isLoaderDismissed()) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
        });
    }

    // Initialize Mapbox/Leaflet mapping setup
    setupItineraryMap(data, destination);
}

/**
 * Configure Leaflet map, plot stops chronologically, draw routing lines, and center views
 */
function setupItineraryMap(data, destination) {
    const mapDiv = document.getElementById('itinerary-map');
    if (!mapDiv) return;

    // 1. Initialize Map instance if not done yet
    if (!itineraryMap) {
        itineraryMap = L.map('itinerary-map', {
            zoomControl: true,
            scrollWheelZoom: false
        });
        
        // Listen to global theme switch to dynamically update map tiles
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('change', () => {
                updateMapTheme();
            });
        }
    }

    // 2. Set/Update Map Tile Layer matching the theme (dark/light base maps)
    updateMapTheme();

    // 3. Clear existing markers and paths from previous plans
    mapMarkers.forEach(marker => itineraryMap.removeLayer(marker));
    mapMarkers = [];
    if (mapRouteLine) {
        itineraryMap.removeLayer(mapRouteLine);
        mapRouteLine = null;
    }

    // 4. Parse coordinates from daily plans chronologically
    const pathCoordinates = [];
    let stopIndex = 0;

    if (data.daily_plans && Array.isArray(data.daily_plans)) {
        data.daily_plans.forEach(day => {
            ['morning', 'afternoon', 'evening'].forEach(period => {
                const slot = day[period];
                if (slot && slot.coordinates && slot.coordinates.lat && slot.coordinates.lng) {
                    const lat = slot.coordinates.lat;
                    const lng = slot.coordinates.lng;
                    const name = slot.activity || (slot.activities && slot.activities[0]) || slot.name || "Destination Stop";
                    const cost = slot.cost || slot.estimated_cost || 0;
                    const time = slot.time || slot.timing || "";
                    const periodName = period.charAt(0).toUpperCase() + period.slice(1);
                    const dayNum = day.day;

                    pathCoordinates.push({ lat, lng, name, periodName, time, cost, dayNum });

                    // Create custom geometric SVG marker
                    const markerHtml = `
                        <div class="custom-map-marker">
                            <div class="marker-pin">
                                <span>${stopIndex + 1}</span>
                            </div>
                        </div>
                    `;
                    
                    const customIcon = L.divIcon({
                         html: markerHtml,
                         className: 'custom-leaflet-marker',
                         iconSize: [30, 30],
                         iconAnchor: [15, 15]
                    });

                    const popupContent = `
                        <div style="font-family: var(--font-body); padding: 5px;">
                            <strong style="color: var(--accent-primary); font-size: 13px; font-weight:700;">Day ${dayNum}: ${name}</strong><br/>
                            <span style="font-size: 11px; color: var(--text-muted);">${periodName} Slot ${time ? `(${time})` : ''}</span><br/>
                            <span style="font-size: 11px; font-weight: 600; color: var(--success);">Cost: ₹${formatNumber(cost)}</span>
                        </div>
                    `;

                    const marker = L.marker([lat, lng], { icon: customIcon })
                        .bindPopup(popupContent)
                        .addTo(itineraryMap);
                    
                    mapMarkers.push(marker);
                    stopIndex++;
                }
            });
        });
    }

    // 5. Connect chronological stops with route line and distance labels
    if (pathCoordinates.length > 1) {
        const latlngs = pathCoordinates.map(pt => [pt.lat, pt.lng]);
        
        mapRouteLine = L.polyline(latlngs, {
            color: '#7c3aed',
            weight: 4,
            opacity: 0.85,
            dashArray: '6, 8',
            lineJoin: 'round'
        }).addTo(itineraryMap);

        // Add distance labels between consecutive stops
        for (let i = 0; i < pathCoordinates.length - 1; i++) {
            const p1 = pathCoordinates[i];
            const p2 = pathCoordinates[i + 1];
            const midLat = (p1.lat + p2.lat) / 2;
            const midLng = (p1.lng + p2.lng) / 2;
            
            // Calculate distance using Haversine
            const dist = haversineDistance(p1.lat, p1.lng, p2.lat, p2.lng);
            
            if (dist > 0.3) { // Only show for distances > 300m
                const distLabel = L.divIcon({
                    html: `<div class="map-distance-label">${dist.toFixed(1)} km</div>`,
                    className: 'distance-label-container',
                    iconSize: [60, 20],
                    iconAnchor: [30, 10]
                });

                const distMarker = L.marker([midLat, midLng], { icon: distLabel })
                    .addTo(itineraryMap);
                mapMarkers.push(distMarker);
            }
        }

        // 6. Fit viewport bounds
        itineraryMap.fitBounds(mapRouteLine.getBounds(), {
            padding: [40, 40],
            animate: true,
            duration: 1.5
        });
    } else if (pathCoordinates.length === 1) {
        itineraryMap.setView([pathCoordinates[0].lat, pathCoordinates[0].lng], 13, {
            animate: true,
            duration: 1.2
        });
    } else {
        // Fallback: Default to city center
        const defaultCenter = [28.6139, 77.2090]; // Delhi center coords
        itineraryMap.setView(defaultCenter, 10);
    }

    // 7. Wire timeline card click events
    wireTimelineInteractions();
}

/**
 * Haversine distance calculation (client-side for map labels)
 */
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

/**
 * Update map tile layers based on day/night mode toggle
 */
function updateMapTheme() {
    if (!itineraryMap) return;

    const isDark = document.body.classList.contains('dark-mode');
    
    // CartoDB base map URLs for Light/Dark themes
    const darkTileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    const lightTileUrl = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
    
    const targetUrl = isDark ? darkTileUrl : lightTileUrl;

    if (mapTileLayer) {
        itineraryMap.removeLayer(mapTileLayer);
    }

    mapTileLayer = L.tileLayer(targetUrl, {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CartoDB</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(itineraryMap);
}

/**
 * Handle card click panning and highlight synchronization
 */
function wireTimelineInteractions() {
    document.querySelectorAll('.time-slot[data-lat]').forEach(slotEl => {
        // Remove duplicate listeners if any
        const newSlotEl = slotEl.cloneNode(true);
        slotEl.parentNode.replaceChild(newSlotEl, slotEl);
        
        newSlotEl.addEventListener('click', () => {
            const lat = parseFloat(newSlotEl.getAttribute('data-lat'));
            const lng = parseFloat(newSlotEl.getAttribute('data-lng'));

            // Sync visual highlights in the DOM timeline
            document.querySelectorAll('.time-slot').forEach(el => el.classList.remove('active-highlight'));
            newSlotEl.classList.add('active-highlight');

            if (itineraryMap) {
                // Smooth fly animation to the marker location
                itineraryMap.flyTo([lat, lng], 15, {
                    animate: true,
                    duration: 1.2
                });

                // Find corresponding map marker and open its descriptive popup
                const matchMarker = mapMarkers.find(marker => {
                    if (!marker.getLatLng) return false;
                    const pos = marker.getLatLng();
                    return Math.abs(pos.lat - lat) < 0.0001 && Math.abs(pos.lng - lng) < 0.0001;
                });
                
                if (matchMarker) {
                    setTimeout(() => {
                        matchMarker.openPopup();
                    }, 400);
                }
            }
        });
    });
}

/**
 * Handle mobile view switcher tabs ("Timeline" vs "Map View")
 */
function setupMobileToggles() {
    const splitLayout = document.querySelector('.itinerary-split-layout');
    const btnTimeline = document.getElementById('btn-show-timeline');
    const btnMap = document.getElementById('btn-show-map');
    
    if (splitLayout && btnTimeline && btnMap) {
        // Enforce default timeline view state
        splitLayout.classList.add('show-timeline');
        splitLayout.classList.remove('show-map');
        btnTimeline.classList.add('active');
        btnMap.classList.remove('active');
        
        btnTimeline.onclick = (e) => {
            e.stopPropagation();
            splitLayout.classList.add('show-timeline');
            splitLayout.classList.remove('show-map');
            btnTimeline.classList.add('active');
            btnMap.classList.remove('active');
        };
        
        btnMap.onclick = (e) => {
            e.stopPropagation();
            splitLayout.classList.remove('show-timeline');
            splitLayout.classList.add('show-map');
            btnTimeline.classList.remove('active');
            btnMap.classList.add('active');
            
            // Re-calculate size dynamically to avoid Leaflet rendering grey squares in hidden containers
            if (itineraryMap) {
                setTimeout(() => {
                    itineraryMap.invalidateSize();
                    // Fit bounds to make sure the route fits perfectly on load
                    if (mapRouteLine) {
                        itineraryMap.fitBounds(mapRouteLine.getBounds(), { padding: [30, 30] });
                    }
                }, 100);
            }
        };
    }
}
