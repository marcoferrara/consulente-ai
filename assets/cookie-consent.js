/*
 * Banner di consenso cookie GDPR (Google Consent Mode v2) + Google Analytics 4
 * Aijò — Consulente AI Sardegna
 *
 * Usato dalle pagine che non hanno una gestione cookie propria (privacy.html,
 * pagine SEO). La home (index.html) ha la sua UI inline ma condivide la stessa
 * chiave di localStorage e la stessa logica di Consent Mode, quindi la scelta
 * dell'utente resta coerente su tutto il sito.
 */
(function () {
  var GA_MEASUREMENT_ID = 'G-KRBFC0QFZQ';
  var COOKIE_LS_KEY = 'aijo_cookie_consent';

  // Google tag: caricato sempre, ma il tracciamento resta "denied" finché non arriva il consenso
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  window.gtag = gtag;

  var gaScript = document.createElement('script');
  gaScript.async = true;
  gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_MEASUREMENT_ID;
  document.head.appendChild(gaScript);

  gtag('js', new Date());
  gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied'
  });
  gtag('config', GA_MEASUREMENT_ID);

  function applyConsent(consent) {
    window.cookiePreferences = consent;
    gtag('consent', 'update', {
      analytics_storage: consent.analytics ? 'granted' : 'denied',
      ad_storage: consent.marketing ? 'granted' : 'denied'
    });
  }

  function salvaConsenso(consent) {
    localStorage.setItem(COOKIE_LS_KEY, JSON.stringify(consent));
    applyConsent(consent);
    nascondiBanner();
  }

  function nascondiBanner() {
    var banner = document.getElementById('cookie-banner');
    if (banner) banner.classList.add('hidden');
    var trigger = document.getElementById('cookie-trigger');
    if (trigger) trigger.classList.remove('hidden');
  }

  function mostraBanner() {
    var banner = document.getElementById('cookie-banner');
    if (banner) banner.classList.remove('hidden');
    var trigger = document.getElementById('cookie-trigger');
    if (trigger) trigger.classList.add('hidden');
  }

  // Crea il markup del banner e del pulsante flottante (stessa struttura della home)
  function creaBannerDOM() {
    var wrapper = document.createElement('div');
    wrapper.innerHTML =
      '<div id="cookie-banner" class="cookie-banner hidden">' +
      '  <div class="cookie-content">' +
      '    <div class="cookie-header">' +
      '      <span class="cookie-icon">🛡️</span>' +
      '      <h3>Consenso Privacy &amp; Cookie</h3>' +
      '    </div>' +
      '    <p class="cookie-text">Utilizziamo i cookie per migliorare il funzionamento del sito e analizzare il traffico. Accettando, acconsenti all\'uso dei cookie analitici. Consulta la nostra <a href="/privacy.html">Privacy &amp; Cookie Policy</a>.</p>' +
      '    <div class="cookie-buttons">' +
      '      <button id="btn-cookie-accept" class="btn-cookie-p" type="button">Accetta Tutti</button>' +
      '      <button id="btn-cookie-reject" class="btn-cookie-sec" type="button">Rifiuta Tutti</button>' +
      '    </div>' +
      '  </div>' +
      '</div>' +
      '<button id="cookie-trigger" class="cookie-trigger hidden" title="Impostazioni Privacy" type="button">' +
      '  <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>' +
      '</button>';

    while (wrapper.firstChild) {
      document.body.appendChild(wrapper.firstChild);
    }

    document.getElementById('btn-cookie-accept').addEventListener('click', function () {
      salvaConsenso({ technical: true, analytics: true, marketing: true });
    });
    document.getElementById('btn-cookie-reject').addEventListener('click', function () {
      salvaConsenso({ technical: true, analytics: false, marketing: false });
    });
    document.getElementById('cookie-trigger').addEventListener('click', mostraBanner);
  }

  document.addEventListener('DOMContentLoaded', function () {
    creaBannerDOM();

    var consentRaw = localStorage.getItem(COOKIE_LS_KEY);
    if (consentRaw) {
      applyConsent(JSON.parse(consentRaw));
      document.getElementById('cookie-trigger').classList.remove('hidden');
    } else {
      setTimeout(mostraBanner, 1000);
    }
  });
})();
