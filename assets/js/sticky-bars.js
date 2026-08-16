/* Measures the sticky bars so the ones below them know where to sit.

   Two custom properties:
     --header-h    height of the site header, 0 when it is not sticky
     --topicnav-h  height of the science topic bar, 0 when the page has none

   Measured rather than hard-coded because both change with the viewport, and
   the header stops being sticky on narrow screens. The stylesheet carries
   fallback values, so a page still looks right if this never runs -- the bars
   are position:sticky in CSS, not positioned by script.

   This lives apart from subnav.js because the topic pages have a topic bar and
   no section bar, and would otherwise have no way to learn the header height. */
(function () {
	'use strict';

	var root = document.documentElement;
	var header = document.querySelector('.site-header');
	var topicnav = document.querySelector('.topicnav');

	function heightIfSticky(el) {
		if (!el) return 0;
		return getComputedStyle(el).position === 'sticky'
			? el.getBoundingClientRect().height
			: 0;
	}

	function measure() {
		root.style.setProperty('--header-h', heightIfSticky(header) + 'px');
		root.style.setProperty('--topicnav-h', heightIfSticky(topicnav) + 'px');
	}

	measure();
	addEventListener('resize', measure);
})();
