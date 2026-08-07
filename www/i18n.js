(function () {
  'use strict';

  var LANGS = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'es', name: 'Español', flag: '🇪🇸' },
    { code: 'pl', name: 'Polski', flag: '🇵🇱' },
    { code: 'ru', name: 'Русский', flag: '🇷🇺' },
    { code: 'zh', name: '中文', flag: '🇨🇳' },
    { code: 'ja', name: '日本語', flag: '🇯🇵' },
    { code: 'ar', name: 'العربية', flag: '🇸🇦' },
    { code: 'he', name: 'עברית', flag: '🇮🇱' }
  ];

  var STORAGE_KEY = 'frettool-lang';
  var currentLang = 'en';
  var translations = {};
  var isRtl = false;

  function detectLang() {
    var saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return saved;
    var browser = (navigator.language || 'en').toLowerCase().split('-')[0];
    for (var i = 0; i < LANGS.length; i++) {
      if (LANGS[i].code === browser) return browser;
    }
    return 'en';
  }

  function loadLang(lang, callback) {
    fetch('locales/' + lang + '.json', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        translations = data || {};
        isRtl = translations.rtl || false;
        if (isRtl) {
          document.documentElement.setAttribute('dir', 'rtl');
        } else {
          document.documentElement.removeAttribute('dir');
        }
        delete translations.rtl;
        currentLang = lang;
        localStorage.setItem(STORAGE_KEY, lang);
        document.documentElement.setAttribute('lang', lang);
        if (callback) callback();
      })
      .catch(function () {
        if (callback) callback();
      });
  }

  function t(key) {
    if (translations[key] !== undefined) return translations[key];
    var parts = key.split('.');
    var node = translations;
    for (var i = 0; i < parts.length; i++) {
      if (node === null || typeof node !== 'object') return undefined;
      node = node[parts[i]];
      if (node === undefined) return undefined;
    }
    return typeof node === 'string' ? node : undefined;
  }

  function setTextPreserveChildren(el, val) {
    for (var n = el.firstChild; n; n = n.nextSibling) {
      if (n.nodeType === 3) {
        n.textContent = val;
        return;
      }
    }
    el.textContent = val;
  }

  function applyTranslations() {
    var els = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var key = el.getAttribute('data-i18n');
      var val = t(key);
      if (val === undefined) continue;
      if (el.tagName === 'HTML' || el.tagName === 'TITLE') {
        el.textContent = val;
      } else if (el.hasAttribute('data-i18n-html')) {
        el.innerHTML = val;
      } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = val;
      } else if (el.children.length === 0) {
        el.textContent = val;
      } else {
        setTextPreserveChildren(el, val);
      }
    }

    var holders = document.querySelectorAll('[data-i18n-placeholder]');
    for (var j = 0; j < holders.length; j++) {
      var h = holders[j];
      var hk = h.getAttribute('data-i18n-placeholder');
      var hv = t(hk);
      if (hv) h.placeholder = hv;
    }
  }

  function buildSelector() {
    var existing = document.getElementById('langSelector');
    if (!existing) return;

    var btn = document.createElement('button');
    btn.className = 'lang-btn';
    btn.setAttribute('aria-label', 'Select language');
    btn.innerHTML = '<svg class="lang-globe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg><span class="lang-current"></span>';

    var dropdown = document.createElement('div');
    dropdown.className = 'lang-dropdown';
    dropdown.style.display = 'none';

    for (var i = 0; i < LANGS.length; i++) {
      var item = document.createElement('button');
      item.className = 'lang-option';
      item.innerHTML = '<span class="lang-flag">' + LANGS[i].flag + '</span><span>' + LANGS[i].name + '</span>';
      item.addEventListener('click', (function (code) {
        return function () {
          closeDropdown();
          if (code === currentLang) return;
          loadLang(code, function () {
            applyTranslations();
            updateCurrentLabel();
          });
        };
      })(LANGS[i].code));
      dropdown.appendChild(item);
    }

    existing.appendChild(btn);
    existing.appendChild(dropdown);

    function openDropdown() {
      dropdown.style.display = 'block';
      existing.classList.add('open');
    }
    function closeDropdown() {
      dropdown.style.display = 'none';
      existing.classList.remove('open');
    }

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (dropdown.style.display === 'block') {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    document.addEventListener('click', function () {
      closeDropdown();
    });

    updateCurrentLabel();
  }

  function updateCurrentLabel() {
    var span = document.querySelector('.lang-current');
    if (!span) return;
    for (var i = 0; i < LANGS.length; i++) {
      if (LANGS[i].code === currentLang) {
        span.textContent = LANGS[i].flag + ' ' + LANGS[i].name;
        break;
      }
    }
    var opts = document.querySelectorAll('.lang-option');
    for (var j = 0; j < opts.length; j++) {
      opts[j].classList.toggle('active', opts[j].textContent.indexOf(LANGS[j].name) >= 0 && LANGS[j].code === currentLang);
    }
  }

  window.i18n = {
    init: function () {
      currentLang = detectLang();
      loadLang(currentLang, function () {
        applyTranslations();
        buildSelector();
      });
    },
    switchLang: function (code) {
      if (code === currentLang) return;
      loadLang(code, function () {
        applyTranslations();
        updateCurrentLabel();
      });
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.i18n.init);
  } else {
    window.i18n.init();
  }
})();
