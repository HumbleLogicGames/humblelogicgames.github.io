// Game intro pages: put the store button for this device first, load YouTube only on click.
(function () {
  var ua = navigator.userAgent;
  var os = /Silk|KF[A-Z]{2,4}\b|Kindle/.test(ua) ? 'amazon'   // Fire tablets
    : /Android/i.test(ua) ? 'android'
    : (/iP(hone|ad|od)/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) ? 'ios' : '';
  var box = document.getElementById('stores');
  if (box && os) {
    var mine = box.querySelector('[data-os="' + os + '"]');
    if (mine) { box.insertBefore(mine, box.firstChild); }
  }
  document.querySelectorAll('.yt').forEach(function (b) {
    b.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + b.dataset.id + '?autoplay=1&rel=0';
      f.allow = 'autoplay; encrypted-media; picture-in-picture';
      f.allowFullscreen = true;
      f.title = 'Game video';
      b.replaceChildren(f);
    }, { once: true });
  });
})();

// PC: play the web game inside the page (iframe). Phones/tablets keep the full-page game (play.html).
(function () {
  var btn = document.getElementById('play');
  if (!btn || !window.matchMedia('(pointer: fine) and (min-width: 900px)').matches) return;
  btn.addEventListener('click', function (ev) {
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button) return;   // new-tab clicks behave as normal links
    ev.preventDefault();
    var box = document.getElementById('player');
    if (!box) {
      box = document.createElement('section');
      box.id = 'player';
      box.className = 'player';
      box.innerHTML =
        '<div class="player-frame"><iframe title="Game" allow="autoplay; fullscreen; gamepad" allowfullscreen></iframe></div>' +
        '<div class="player-bar"><button type="button" class="fs">⛶ Full screen</button>' +
        '<a class="tab" href="' + btn.getAttribute('href') + '" target="_blank" rel="noopener">Open in a new tab ↗</a></div>';
      var hero = document.querySelector('.hero');
      hero.parentNode.insertBefore(box, hero.nextSibling);
      var f = box.querySelector('iframe');
      f.src = btn.getAttribute('href');
      f.addEventListener('load', function () { f.focus(); });
      box.querySelector('.fs').addEventListener('click', function () {
        var el = box.querySelector('.player-frame');
        (el.requestFullscreen || el.webkitRequestFullscreen || function () {}).call(el);
        f.focus();
      });
      document.body.classList.add('playing');
    }
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
})();
