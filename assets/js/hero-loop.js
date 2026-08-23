/* Replay only the tail of a video, not the whole clip.

   The hero animation forms the project's name once and then breathes -- the
   wavelength drifting a little either side of where the reveal landed. That
   tail is built to be replayed on its own (see WordSweep.state in
   application_plots/diffraction_animation.py: a whole number of sine cycles,
   so the seek back matches in value and in slope). Looping the whole clip
   instead would dissolve the name and re-form it every few seconds, which is
   the thing the reveal render exists to avoid.

   `data-loop-from` is the fraction of the clip at which the tail begins. A
   fraction rather than a timestamp: the encoded duration is the authority, not
   the frame count the generator was asked for.

   Without this script the video plays through once and stops on the word --
   exactly what it did before the tail existed. Reduced motion is left alone:
   reduced-motion.js has already paused it and exposed controls, and seeking a
   paused video would fight that. */
(function () {
	'use strict';

	if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

	document.querySelectorAll('video[data-loop-from]').forEach(function (v) {
		var frac = parseFloat(v.getAttribute('data-loop-from'));
		if (!(frac >= 0 && frac < 1)) return;

		v.addEventListener('ended', function () {
			if (!v.duration) return;
			v.currentTime = v.duration * frac;
			v.play();
		});
	});
})();
