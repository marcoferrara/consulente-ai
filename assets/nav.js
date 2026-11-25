/* Barra di navigazione: diventa scura dopo lo scroll, come nella home */
(function () {
  'use strict';
  var nav = document.getElementById('nav');
  if (!nav) return;
  function update() { nav.classList.toggle('scrolled', window.scrollY > 60); }
  window.addEventListener('scroll', update, { passive: true });
  update();
})();
