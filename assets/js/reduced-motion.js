// Honour prefers-reduced-motion for autoplaying figures: pause them, and expose
// controls so the reader can still watch if they choose. Without the controls
// the setting would simply remove the content rather than hand it over.
(function () {
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.querySelectorAll('video[autoplay]').forEach(function (v) {
    v.removeAttribute('autoplay');
    v.controls = true;
    v.pause();
  });
})();
