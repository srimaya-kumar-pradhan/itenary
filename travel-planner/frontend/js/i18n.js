/**
 * I18nManager — Client-side Internationalization Engine
 *
 * Features:
 *  • Static dictionary translations for all supported languages
 *  • Bhashini ULCA API integration (via backend proxy) for Indian languages
 *  • Smooth text-fade transitions on language switch
 *  • MutationObserver for auto-translating dynamically rendered content
 *  • RTL support for Arabic
 *  • Zero interference with existing script.js business logic
 */

class I18nManager {
    constructor() {
        this.currentLang = 'en';
        this.defaultLang = 'en';
        this.translations = typeof TRANSLATIONS !== 'undefined' ? TRANSLATIONS : {};
        this.originalTexts = new Map();
        this.observer = null;
        this.API_BASE = 'http://localhost:8000';
        this._bhashiniCache = new Map();
        this._transitioning = false;
    }

    /* ──────────────────────────────────────
       INITIALIZATION
       ────────────────────────────────────── */

    init() {
        // Store originals on first run
        this._captureOriginals();

        // Build language selector UI
        this._buildLanguageSelector();

        // Set up MutationObserver for dynamic content (results rendered by script.js)
        this._setupObserver();

        // Check localStorage for saved language preference
        const saved = localStorage.getItem('travelPlanner_lang');
        if (saved && this.translations[saved]) {
            this.setLanguage(saved, false);
        }
    }

    /* ──────────────────────────────────────
       CAPTURE ORIGINAL ENGLISH TEXT
       ────────────────────────────────────── */

    _captureOriginals() {
        // Text content elements
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            this.originalTexts.set(key, el.textContent.trim());
        });

        // Placeholder elements
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            this.originalTexts.set(key, el.getAttribute('placeholder') || '');
        });

        // Select option elements
        document.querySelectorAll('[data-i18n-option]').forEach(el => {
            const key = el.getAttribute('data-i18n-option');
            this.originalTexts.set(key, el.textContent.trim());
        });
    }

    /* ──────────────────────────────────────
       TRANSLATION LOOKUP
       ────────────────────────────────────── */

    t(key) {
        const lang = this.currentLang;

        // Try current language
        if (this.translations[lang] && this.translations[lang][key]) {
            return this.translations[lang][key];
        }

        // Fall back to English
        if (this.translations.en && this.translations.en[key]) {
            return this.translations.en[key];
        }

        // Fall back to stored original
        return this.originalTexts.get(key) || key;
    }

    /* ──────────────────────────────────────
       SET LANGUAGE
       ────────────────────────────────────── */

    async setLanguage(langCode, animate = true) {
        if (!this.translations[langCode]) return;
        if (this._transitioning) return;

        const prevLang = this.currentLang;
        this.currentLang = langCode;
        localStorage.setItem('travelPlanner_lang', langCode);

        // Update selector UI
        this._updateSelectorDisplay(langCode);

        // Handle RTL/LTR
        const meta = this.translations[langCode]._meta || {};
        document.documentElement.dir = meta.dir || 'ltr';
        document.documentElement.lang = langCode;

        if (animate) {
            this._transitioning = true;
            await this._fadeTranslate();
            this._transitioning = false;
        } else {
            this._applyTranslations();
        }

        // For Indian languages with missing keys, try Bhashini API
        if (meta.group === 'indian' && langCode !== 'en') {
            this._translateMissingViaBhashini(langCode);
        }
    }

    /* ──────────────────────────────────────
       APPLY TRANSLATIONS TO DOM
       ────────────────────────────────────── */

    _applyTranslations() {
        // Text content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });

        // Placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.setAttribute('placeholder', this.t(key));
        });

        // Select options
        document.querySelectorAll('[data-i18n-option]').forEach(el => {
            const key = el.getAttribute('data-i18n-option');
            el.textContent = this.t(key);
        });
    }

    /* ──────────────────────────────────────
       SMOOTH FADE TRANSITION
       ────────────────────────────────────── */

    async _fadeTranslate() {
        const translatables = document.querySelectorAll('[data-i18n], [data-i18n-option]');

        // Fade out
        translatables.forEach(el => {
            el.style.transition = 'opacity 0.2s ease-in-out';
            el.style.opacity = '0';
        });

        await this._wait(220);

        // Apply translations
        this._applyTranslations();

        // Fade in
        translatables.forEach(el => {
            el.style.opacity = '1';
        });

        await this._wait(220);

        // Clean up inline styles
        translatables.forEach(el => {
            el.style.removeProperty('transition');
            el.style.removeProperty('opacity');
        });
    }

    _wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /* ──────────────────────────────────────
       BHASHINI API INTEGRATION
       (via backend proxy at /api/translate)
       ────────────────────────────────────── */

    async _translateMissingViaBhashini(targetLang) {
        const langDict = this.translations[targetLang] || {};
        const enDict = this.translations.en || {};
        const missingKeys = [];
        const missingTexts = [];

        // Collect keys that exist in English but not in target
        for (const key of Object.keys(enDict)) {
            if (key === '_meta') continue;
            if (!langDict[key]) {
                missingKeys.push(key);
                missingTexts.push(enDict[key]);
            }
        }

        if (missingTexts.length === 0) return;

        // Check cache
        const cacheKey = `bhashini_${targetLang}`;
        if (this._bhashiniCache.has(cacheKey)) {
            const cached = this._bhashiniCache.get(cacheKey);
            missingKeys.forEach((key, i) => {
                if (cached[key]) {
                    this.translations[targetLang][key] = cached[key];
                }
            });
            this._applyTranslations();
            return;
        }

        try {
            const response = await fetch(`${this.API_BASE}/api/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    texts: missingTexts,
                    source_lang: 'en',
                    target_lang: targetLang,
                }),
            });

            if (!response.ok) return;

            const data = await response.json();
            if (data.translations && data.translations.length === missingKeys.length) {
                const cacheEntry = {};
                missingKeys.forEach((key, i) => {
                    this.translations[targetLang][key] = data.translations[i];
                    cacheEntry[key] = data.translations[i];
                });
                this._bhashiniCache.set(cacheKey, cacheEntry);
                this._applyTranslations();
            }
        } catch (err) {
            // Bhashini unavailable — silently keep English fallback for missing keys
            console.log('Bhashini translation unavailable, using static dictionary:', err.message);
        }
    }

    /**
     * Translate arbitrary dynamic text (e.g., itinerary results).
     * Used by the MutationObserver for dynamically rendered content.
     */
    async translateDynamic(texts, targetLang) {
        if (!texts.length || targetLang === 'en') return texts;

        try {
            const response = await fetch(`${this.API_BASE}/api/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    texts: texts,
                    source_lang: 'en',
                    target_lang: targetLang,
                }),
            });

            if (!response.ok) return texts;
            const data = await response.json();
            return data.translations || texts;
        } catch {
            return texts;
        }
    }

    /* ──────────────────────────────────────
       MUTATION OBSERVER — Dynamic Content
       ────────────────────────────────────── */

    _setupObserver() {
        const targets = ['summary-grid', 'hotel-details', 'daily-plans',
                         'budget-breakdown', 'hidden-gems', 'travel-tips',
                         'emergency-contacts'];

        this.observer = new MutationObserver((mutations) => {
            if (this.currentLang === 'en') return;

            for (const mutation of mutations) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    this._translateDynamicContent(mutation.target);
                }
            }
        });

        targets.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                this.observer.observe(el, { childList: true, subtree: true });
            }
        });
    }

    async _translateDynamicContent(container) {
        if (this.currentLang === 'en') return;

        // Collect visible text nodes in the dynamic container
        const textEls = container.querySelectorAll(
            '.slot-activity, .slot-description, .gem-name, .gem-description, ' +
            '.day-title, .hotel-name, .hotel-location'
        );

        if (textEls.length === 0) return;

        const texts = Array.from(textEls).map(el => el.textContent.trim()).filter(t => t.length > 0);
        if (texts.length === 0) return;

        const translated = await this.translateDynamic(texts, this.currentLang);

        let idx = 0;
        textEls.forEach(el => {
            const original = el.textContent.trim();
            if (original.length > 0 && translated[idx]) {
                el.style.transition = 'opacity 0.2s ease-in-out';
                el.style.opacity = '0';
                setTimeout(() => {
                    el.textContent = translated[idx];
                    el.style.opacity = '1';
                    idx++;
                }, 200);
            } else {
                idx++;
            }
        });
    }

    /* ──────────────────────────────────────
       LANGUAGE SELECTOR UI
       ────────────────────────────────────── */

    _buildLanguageSelector() {
        const container = document.createElement('div');
        container.className = 'lang-selector';
        container.id = 'lang-selector';

        // Current language display (the button)
        const currentBtn = document.createElement('button');
        currentBtn.className = 'lang-current';
        currentBtn.id = 'lang-current-btn';
        currentBtn.type = 'button';

        const meta = this.translations.en._meta;
        currentBtn.innerHTML = `<span class="lang-flag">${meta.flag}</span><span class="lang-name">EN</span><span class="lang-arrow">▾</span>`;

        // Dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'lang-dropdown';
        dropdown.id = 'lang-dropdown';

        // Group languages
        const indianLangs = [];
        const intlLangs = [];

        for (const [code, dict] of Object.entries(this.translations)) {
            const m = dict._meta;
            if (!m) continue;
            if (m.group === 'indian') indianLangs.push({ code, ...m });
            else intlLangs.push({ code, ...m });
        }

        // Indian group
        if (indianLangs.length > 0) {
            const groupLabel = document.createElement('div');
            groupLabel.className = 'lang-group-label';
            groupLabel.textContent = '🇮🇳 Indian Languages';
            dropdown.appendChild(groupLabel);

            indianLangs.forEach(lang => {
                dropdown.appendChild(this._createLangOption(lang));
            });
        }

        // International group
        if (intlLangs.length > 0) {
            const groupLabel = document.createElement('div');
            groupLabel.className = 'lang-group-label';
            groupLabel.textContent = '🌍 International';
            dropdown.appendChild(groupLabel);

            intlLangs.forEach(lang => {
                dropdown.appendChild(this._createLangOption(lang));
            });
        }

        // Toggle dropdown
        currentBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('open');
        });

        // Close on outside click
        document.addEventListener('click', () => {
            dropdown.classList.remove('open');
        });

        container.appendChild(currentBtn);
        container.appendChild(dropdown);
        document.body.appendChild(container);
    }

    _createLangOption(lang) {
        const opt = document.createElement('button');
        opt.className = 'lang-option';
        opt.type = 'button';
        opt.setAttribute('data-lang', lang.code);
        opt.innerHTML = `<span class="lang-flag">${lang.flag}</span><span>${lang.name}</span>`;

        opt.addEventListener('click', (e) => {
            e.stopPropagation();
            this.setLanguage(lang.code);
            document.getElementById('lang-dropdown').classList.remove('open');
        });

        return opt;
    }

    _updateSelectorDisplay(langCode) {
        const meta = this.translations[langCode]._meta;
        const btn = document.getElementById('lang-current-btn');
        if (btn && meta) {
            btn.innerHTML = `<span class="lang-flag">${meta.flag}</span><span class="lang-name">${langCode.toUpperCase()}</span><span class="lang-arrow">▾</span>`;
        }

        // Highlight active option
        document.querySelectorAll('.lang-option').forEach(opt => {
            opt.classList.toggle('active', opt.getAttribute('data-lang') === langCode);
        });
    }
}

// ─── AUTO-INITIALIZE ───
document.addEventListener('DOMContentLoaded', () => {
    window.i18n = new I18nManager();
    window.i18n.init();
});
