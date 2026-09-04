/* Filter a long list down to what someone is looking for.
 *
 * Modelled on the publication filter on the hi_class site, and deliberately
 * the same shape: no index, no library, no fuzzy matching. The searchable text
 * of every entry is its own textContent, lowercased and cached once on load,
 * and a query is a substring test against it. For a few hundred entries that
 * is instantaneous, and it means an entry is searchable by everything it
 * shows -- title, author, journal, arXiv number, speaker, place -- without a
 * single field having to be declared anywhere.
 *
 * The markup contract, all data attributes so nothing depends on class names:
 *
 *   [data-search]                 the container, one per filterable list
 *     [data-search-noun]          plural noun for the count ("articles")
 *     [data-search-ui]            the toolbar, `hidden` in the markup
 *       [data-search-input]       the input
 *       [data-search-facet]       optional checkbox, value = a kind to show
 *       [data-search-count]       aria-live count
 *     [data-search-group]         a year block, hidden when it empties
 *       [data-search-item]        one entry
 *         [data-search-kind]      optional, the value a facet checkbox matches
 *     [data-search-empty]         the empty state, `hidden` in the markup
 *
 * Facets are optional and additive: a list with no [data-search-facet] behaves
 * exactly as it did before they existed. Where they are used, an entry has to
 * pass both the text query and a ticked box, and unticking everything shows
 * nothing rather than everything -- which is what the boxes say, and guessing
 * otherwise would be a filter that ignores the reader.
 *
 * Two things are load-bearing rather than decorative:
 *
 * 1. The toolbar is `hidden` in the HTML and unhidden here. With JavaScript
 *    off the list still renders in full, and no search box is offered that
 *    cannot work. An inert input is worse than no input.
 * 2. Totals are counted from the DOM, never written into the template, so
 *    they cannot fall out of step with _data/publications.yml.
 */
(function () {
  'use strict';

  var containers = document.querySelectorAll('[data-search]');

  Array.prototype.forEach.call(containers, function (root) {
    var ui    = root.querySelector('[data-search-ui]');
    var input = root.querySelector('[data-search-input]');
    var count = root.querySelector('[data-search-count]');
    var empty = root.querySelector('[data-search-empty]');
    if (!ui || !input || !count) { return; }

    var noun   = root.getAttribute('data-search-noun') || 'entries';
    var facets = Array.prototype.slice.call(root.querySelectorAll('[data-search-facet]'));
    var groups = Array.prototype.slice.call(root.querySelectorAll('[data-search-group]'));

    // Cache the searchable text of every entry once, up front.
    var items = [];
    groups.forEach(function (group) {
      var entries = Array.prototype.slice.call(group.querySelectorAll('[data-search-item]'));
      entries.forEach(function (el) {
        items.push({
          el: el,
          text: el.textContent.toLowerCase(),
          kind: el.getAttribute('data-search-kind') || ''
        });
      });
      group._entries = entries;
    });

    var total = items.length;
    if (!total) { return; }

    function render(shown) {
      count.innerHTML = shown === total
        ? '<b>' + total + '</b> ' + noun
        : '<b>' + shown + '</b> of ' + total + ' ' + noun;
      if (empty) { empty.hidden = shown !== 0; }
    }

    function filter() {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      var kinds = facets.length
        ? facets.filter(function (f) { return f.checked; })
                .map(function (f) { return f.value; })
        : null;

      items.forEach(function (item) {
        var hit = (q === '' || item.text.indexOf(q) !== -1) &&
                  (kinds === null || kinds.indexOf(item.kind) !== -1);
        item.el.hidden = !hit;
        if (hit) { shown++; }
      });

      // Hide a year heading once all of its entries are filtered out.
      groups.forEach(function (group) {
        group.hidden = !group._entries.some(function (el) { return !el.hidden; });
      });

      render(shown);
    }

    input.addEventListener('input', filter);
    facets.forEach(function (f) { f.addEventListener('change', filter); });
    ui.hidden = false;
    render(total);
  });
})();
