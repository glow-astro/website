/* In-page section navigation: keeps the sticky bar clear of the site header
   and marks the section currently in view. Degrades to a plain list of anchor
   links if this never runs. */
(function () {
	'use strict';

	var nav = document.querySelector('[data-subnav]');
	if (!nav) return;

	var root = document.documentElement;

	/* --header-h and --topicnav-h come from sticky-bars.js, which runs on every
	   page; this only needs to publish its own height for scroll-margin-top. */
	function measure() {
		root.style.setProperty('--subnav-h', nav.getBoundingClientRect().height + 'px');
	}

	var links = Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]'));
	var targets = links.map(function (a) {
		try {
			return document.getElementById(decodeURIComponent(a.hash.slice(1)));
		} catch (e) {
			return null;
		}
	});

	var current = null;

	function highlight() {
		/* The active section is the last one whose top has passed under the
		   two sticky bars. */
		/* Slack must cover the sections' scroll-margin-top, or the section you
		   just jumped to sits below the cutoff and the previous one stays lit. */
		var cutoff = nav.getBoundingClientRect().bottom + 20;
		var found = -1;
		for (var i = 0; i < targets.length; i++) {
			if (targets[i] && targets[i].getBoundingClientRect().top <= cutoff) found = i;
		}
		/* A short final section never reaches the cutoff, so scrolling to the
		   foot of the page would leave the previous one lit. At the bottom,
		   the last section is the one you are looking at. */
		if (innerHeight + scrollY >= root.scrollHeight - 2) {
			for (var j = targets.length - 1; j >= 0; j--) {
				if (targets[j]) { found = j; break; }
			}
		}
		if (found === current) return;
		if (current !== null && links[current]) links[current].removeAttribute('aria-current');
		if (found >= 0) links[found].setAttribute('aria-current', 'true');
		current = found;
	}

	var ticking = false;
	function onScroll() {
		if (ticking) return;
		ticking = true;
		requestAnimationFrame(function () {
			highlight();
			ticking = false;
		});
	}

	measure();
	highlight();
	addEventListener('scroll', onScroll, { passive: true });
	addEventListener('resize', function () {
		measure();
		highlight();
	});
})();
