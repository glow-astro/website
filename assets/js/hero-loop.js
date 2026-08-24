/* Hand a hero animation over from its one-shot clip to its looping one.

   The name resolves once and then breathes, and those are different jobs: the
   reveal must never repeat, the breathing must never stop. One clip cannot do
   both. `loop` would replay the reveal, and seeking past it does not work
   either -- the encoder gives a clip a single keyframe for its whole length
   (application_plots/utils/anim_encode.py sets -g to the frame count), so a
   seek into the middle resolves to the start. That was tried, and it replayed
   the reveal every six seconds.

   So there are two <video> elements stacked in [data-hero-loop]: the first
   autoplays once, the second loops. They meet on the same frame, so swapping
   opacity at the join shows nothing.

   The second is fetched when the first starts playing, which is about six and a
   half seconds of head start for 0.6 MB, rather than at page load where it
   would compete with the clip actually on screen.

   Degrades to the first clip playing once and stopping on the word -- what the
   page did before the breathing existed. Reduced motion is left alone:
   reduced-motion.js has paused the reveal and exposed controls, and starting a
   loop over the top of that would be exactly what the setting asks us not to
   do. */
(function () {
	'use strict';

	if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

	document.querySelectorAll('[data-hero-loop]').forEach(function (stack) {
		var clips = stack.querySelectorAll('video');
		if (clips.length !== 2) return;
		var reveal = clips[0], breathe = clips[1];

		reveal.addEventListener('playing', function () {
			if (breathe.preload !== 'auto') {
				breathe.preload = 'auto';
				breathe.load();
			}
		}, { once: true });

		reveal.addEventListener('ended', function () {
			var start = breathe.play();
			// Only reveal it once it is actually running; a rejected play()
			// would otherwise leave a blank box where the word was.
			if (start && start.then) {
				start.then(function () { stack.classList.add('is-looping'); })
				     .catch(function () { /* keep the held last frame */ });
			} else {
				stack.classList.add('is-looping');
			}
		});
	});
})();
