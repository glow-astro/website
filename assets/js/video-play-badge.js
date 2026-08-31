/* Mark an on-demand figure as idle, so CSS can show a play badge over it.
 *
 * The badge itself is entirely in main.css (.video-frame). All this does is
 * say whether the video is running, which CSS cannot ask on its own: the
 * `:paused` pseudo-class would have done it with no script at all, and does
 * in Firefox and Safari, but Chrome 151 still does not support it. Tested,
 * not assumed -- `CSS.supports('selector(video:paused)')` is false there.
 *
 * `data-idle` is set here rather than defaulted in the markup so that a
 * reader without JavaScript sees no badge at all. The native `controls` bar
 * is still there and still works, which is exactly the behaviour this
 * replaces: the fallback is the status quo, never a dead control.
 *
 * Ended counts as idle on purpose. These figures stop on their last frame,
 * so the badge coming back reads as "play it again" over the finished plot.
 */
(function () {
  'use strict';

  var frames = document.querySelectorAll('.video-frame');

  Array.prototype.forEach.call(frames, function (frame) {
    var video = frame.querySelector('video');
    if (!video) { return; }

    function idle(on) {
      if (on) { frame.setAttribute('data-idle', ''); }
      else    { frame.removeAttribute('data-idle'); }
    }

    /* The badge is the only part of the frame that takes clicks, and only
       while idle, so this cannot swallow a click meant for the control bar:
       that sits at the bottom edge, well outside a 72px disc in the middle.
       A click anywhere else reaches the video as before. */
    frame.addEventListener('click', function (event) {
      if (event.target !== frame) { return; }
      video.play();
    });

    video.addEventListener('play',    function () { idle(false); });
    video.addEventListener('playing', function () { idle(false); });
    video.addEventListener('pause',   function () { idle(true); });
    video.addEventListener('ended',   function () { idle(true); });

    idle(video.paused);
  });
})();
