/* Send off-site links, and the site's own PDFs, to a new tab, so a visitor
   reading a page is never navigated away from it. A PDF replaces the page in
   the same way an off-site link does -- the CV, the theses and the course
   material all belong in a tab of their own.

   Done here rather than in the templates because the links are spread across
   nine pages and half a dozen data files, and one rule cannot be forgotten the
   way two hundred attributes can. Without JavaScript the links still work;
   they just open in place.

   rel="noopener" is set alongside: a new tab opened this way can otherwise
   reach back at this page through window.opener. */
(function () {
	'use strict';

	var here = location.host;

	Array.prototype.forEach.call(
		document.querySelectorAll('a[href]'),
		function (a) {
			// Leaves mailto: and in-page fragments alone.
			if (a.protocol !== 'http:' && a.protocol !== 'https:') return;
			if (!a.host) return;
			if (a.hasAttribute('target')) return;

			var offsite = a.host !== here;
			var document_file = /\.(pdf|ps|zip|tar\.gz|tgz)$/i.test(a.pathname);
			if (!offsite && !document_file) return;

			a.target = '_blank';
			var rel = (a.getAttribute('rel') || '').split(/\s+/).filter(Boolean);
			if (rel.indexOf('noopener') === -1) rel.push('noopener');
			a.setAttribute('rel', rel.join(' '));
		}
	);
})();
