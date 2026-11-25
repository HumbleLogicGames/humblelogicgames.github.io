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
