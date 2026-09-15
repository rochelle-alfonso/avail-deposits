/* Avail Deposits — page behaviour.
 *
 * Five independent IIFEs: mobile nav, deposit-flow tabs, the configurator
 * panel's intersection gate, the FAQ accordion, and the scroll observers.
 * Loaded with `defer`, so it runs after the document is parsed - it used to
 * sit inline at the end of <body>, which gave it the same guarantee.
 */
// Mobile nav — the Menu button opens the slide-in panel, the way the live
// nav does: label flips to Close, an overlay dims the page, body scroll locks,
// and the panel is pinned to the bottom edge of the header.
(function () {
  var toggle  = document.getElementById('navMenu');
  var menu    = document.getElementById('mobileMenu');
  var overlay = document.getElementById('mobileMenuOverlay');
  var label   = toggle && toggle.querySelector('.nav-menu__label');
  if (!toggle || !menu) return;

  function position() {
    var header = document.querySelector('.nav-header');
    if (!header) return;
    menu.style.setProperty('--mobile-menu-top',
      (header.getBoundingClientRect().bottom + window.scrollY) + 'px');
  }

  function setOpen(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    if (label) label.textContent = open ? 'Close' : 'Menu';
    if (open) position();                 // measure before the panel is shown
    menu.hidden = !open;
    if (overlay) overlay.hidden = !open;
    document.body.classList.toggle('menu-open', open);
  }

  var close = document.createElement('button');
  close.className = 'mobile-menu__close';
  close.type = 'button';
  close.setAttribute('aria-label', 'Close menu');
  close.addEventListener('click', function () { setOpen(false); });
  var nav = menu.querySelector('.mobile-menu__nav');
  (nav || menu).insertBefore(close, (nav || menu).firstChild);

  toggle.addEventListener('click', function () {
    setOpen(toggle.getAttribute('aria-expanded') !== 'true');
  });
  if (overlay) overlay.addEventListener('click', function () { setOpen(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !menu.hidden) { setOpen(false); toggle.focus(); }
  });

  var t;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(function () {
      if (window.innerWidth > 1000 && !menu.hidden) setOpen(false);
      else if (!menu.hidden) position();
    }, 150);
  });
})();

// Desktop dropdowns open on hover and focus in CSS. The only thing left for
// script is keeping aria-expanded honest about what is actually on screen.
(function () {
  Array.prototype.forEach.call(document.querySelectorAll('.nav-dropdown'), function (item) {
    var trigger = item.querySelector('.nav-links__trigger');
    if (!trigger) return;
    function sync(open) { trigger.setAttribute('aria-expanded', String(open)); }
    item.addEventListener('pointerenter', function () { sync(true); });
    item.addEventListener('pointerleave', function () { sync(false); });
    item.addEventListener('focusin',  function () { sync(true); });
    item.addEventListener('focusout', function (e) {
      if (!item.contains(e.relatedTarget)) sync(false);
    });
    // a trigger press is a no-op for the menu, so don't let it submit or scroll
    trigger.addEventListener('click', function (e) { e.preventDefault(); });
  });
})();

// Flow tabs — a section's clips are one continuous run, so each hands off to
// the next before it finishes. The outgoing and incoming clips overlap for the
// length of the fade, which turns the join into a cross-dissolve rather than
// a cut, and a single pill slides between tabs to match.
//
// Runs once per .flow section and takes its order from that section's own tabs,
// so a page carrying more than one of these (the deposit run and the funded-
// position run) drives each independently instead of the first one winning.
Array.prototype.slice.call(document.querySelectorAll('.flow')).forEach(function (section) {
  var tabsEl = section.querySelector('.tabs');
  var tabs = Array.prototype.slice.call(section.querySelectorAll('.tab'));
  var clips = Array.prototype.slice.call(section.querySelectorAll('.flow__video'));
  var panel = section.querySelector('.flow__panel');
  if (!tabsEl || !panel || !tabs.length || !clips.length) return;

  var order = tabs.map(function (t) { return t.dataset.seg; });
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  // The 1642px clips exist so the 821px panel lands at exactly 2x on retina.
  // Phones, and any display below 1.5 DPR, are served the lighter 1280px cut.
  var small = (window.matchMedia && matchMedia('(max-width: 700px)').matches)
           || (window.devicePixelRatio || 1) < 1.5;

  var FADE = 550;      // must match the .flow__video transition
  var LEAD = 0.55;     // start the next clip this early so the two overlap
  var current = order[0];

  function pick(v) { return (small && v.dataset.srcSm) || v.dataset.src; }
  function clipFor(seg) {
    for (var i = 0; i < clips.length; i++) if (clips[i].dataset.seg === seg) return clips[i];
  }
  function tabFor(seg) {
    for (var i = 0; i < tabs.length; i++) if (tabs[i].dataset.seg === seg) return tabs[i];
  }
  // the markup ships preload="none" so parsing costs nothing; a clip only
  // opts into a real prefetch at the moment we decide to load it
  function load(v) {
    if (!v || v.getAttribute('src')) return;
    v.preload = 'auto';
    v.setAttribute('src', pick(v));
  }
  function next(seg) { return order[(order.indexOf(seg) + 1) % order.length]; }
  // A play() issued while the clip is still fetching is aborted by the load
  // ("interrupted by a new load request") and the promise rejects, which used
  // to leave the run stalled on a paused first frame with nothing to restart
  // it. On the live page the two observers below fire a screenful apart so the
  // data is usually there in time; anywhere the panel is near the top of the
  // page, or the network is slow, they land in the same tick. Retry once the
  // clip actually has data.
  function tryPlay(v) {
    if (!v || still) return;
    var p;
    try { p = v.play(); } catch (e) { return; }
    if (!p || !p.catch) return;
    p.catch(function () {
      v.addEventListener('canplay', function once() {
        v.removeEventListener('canplay', once);
        if (v.dataset.seg !== current) return;
        try { v.play(); } catch (e) {}
      });
    });
  }

  // ---- sliding pill ----
  var pill = document.createElement('span');
  pill.className = 'tabs__pill';
  tabsEl.insertBefore(pill, tabsEl.firstChild);
  tabsEl.classList.add('tabs--pill');

  function movePill(animate) {
    var t = tabFor(current);
    if (!t) return;
    pill.style.transition = animate ? '' : 'none';
    pill.style.width = t.offsetWidth + 'px';
    pill.style.transform = 'translateX(' + t.offsetLeft + 'px)';
    if (!animate) { void pill.offsetWidth; pill.style.transition = ''; }
  }
  function keepVisible(t) {
    if (tabsEl.scrollWidth <= tabsEl.clientWidth) return;
    var l = t.offsetLeft, r = l + t.offsetWidth;
    if (l < tabsEl.scrollLeft) tabsEl.scrollTo({ left: Math.max(0, l - 12), behavior: 'smooth' });
    else if (r > tabsEl.scrollLeft + tabsEl.clientWidth)
      tabsEl.scrollTo({ left: r - tabsEl.clientWidth + 12, behavior: 'smooth' });
  }

  // ---- switching ----
  function show(seg) {
    current = seg;
    tabs.forEach(function (t) { t.setAttribute('aria-selected', String(t.dataset.seg === seg)); });
    movePill(true);                                    // move now...
    requestAnimationFrame(function () { movePill(true); });  // ...and settle after any reflow
    keepVisible(tabFor(seg));

    clips.forEach(function (v) {
      var on = v.dataset.seg === seg;
      v.classList.toggle('is-on', on);
      v.setAttribute('aria-hidden', String(!on));
      if (!on) return;                       // the outgoing clip keeps playing under the fade
      load(v);
      v.__handedOff = false;
      if (still) return;
      try { v.currentTime = 0; } catch (e) {}
      tryPlay(v);
    });

    // once the dissolve is over, park whatever is no longer on screen
    clearTimeout(show.__t);
    show.__t = setTimeout(function () {
      clips.forEach(function (v) {
        if (v.dataset.seg === current) return;
        v.pause();
        try { v.currentTime = 0; } catch (e) {}
      });
    }, FADE + 60);

    load(clipFor(next(seg)));                // warm the next one while this plays
  }

  clips.forEach(function (v) {
    // hand off slightly before the end so the clips overlap
    v.addEventListener('timeupdate', function () {
      if (still || v.dataset.seg !== current || v.__handedOff) return;
      if (!isFinite(v.duration) || !v.duration) return;
      if (v.duration - v.currentTime <= LEAD) { v.__handedOff = true; show(next(current)); }
    });
    // fallbacks: a clip that runs out or fails shouldn't strand the loop
    v.addEventListener('ended', function () {
      if (still || v.dataset.seg !== current || v.__handedOff) return;
      v.__handedOff = true; show(next(current));
    });
    v.addEventListener('error', function () {
      if (still || v.dataset.seg !== current) return;
      show(next(current));
    });
  });

  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { show(t.dataset.seg); });
    t.addEventListener('keydown', function (e) {
      var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      e.preventDefault();
      var n = tabs[(i + d + tabs.length) % tabs.length];
      n.focus(); show(n.dataset.seg);
    });
  });

  // ---- start ----
  // Nothing here is fetched at parse time. The panel sits well below the fold,
  // so the posters and the first clips only start downloading once the section
  // is close enough to be worth it.
  clips[0].classList.add('is-on');
  movePill(false);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { movePill(false); });
  if (window.ResizeObserver) new ResizeObserver(function () { movePill(false); }).observe(tabsEl);

  var armed = false;
  function arm() {
    if (armed) return;
    armed = true;
    clips.forEach(function (v) { if (v.dataset.poster) v.poster = v.dataset.poster; });
    load(clipFor(current));
    load(clipFor(next(current)));
  }

  // a tab press before the section is armed still has to work
  tabs.forEach(function (t) { t.addEventListener('click', arm); });

  if (window.IntersectionObserver) {
    // start the download a screenful early, so the first clip is ready by the
    // time the panel actually arrives
    new IntersectionObserver(function (entries, obs) {
      if (!entries.some(function (e) { return e.isIntersecting; })) return;
      arm(); obs.disconnect();
    }, { rootMargin: '400px 0px' }).observe(panel);

    // ...but only run the loop while the panel is genuinely on screen
    if (!still) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          var v = clipFor(current);
          if (!v) return;
          if (e.isIntersecting) tryPlay(v);
          else v.pause();
        });
      }, { threshold: 0.2 }).observe(panel);
    }
  } else {
    arm();
    if (!still) tryPlay(clips[0]);
  }
});

// Hero film — the prediction page's hero is a looping clip rather than a still.
// The one thing to get right is what it sits on when it is NOT playing. Frame 0
// is an empty deposit card, because the loop has to end where it begins, and
// that is the worst possible thing to leave on screen. So any time the film is
// not running — reduced motion, a refused autoplay, a background tab — it parks
// inside the last hold instead, where the card reads as funded.
(function () {
  var film = document.querySelector('.deposit-hero__film');
  if (!film) return;
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function park() {
    try { film.currentTime = Math.max(0, (film.duration || 8.4) - 1.6); } catch (e) {}
    film.pause();
  }
  function whenReady(fn) {
    if (film.readyState >= 1) fn();
    else film.addEventListener('loadedmetadata', fn, { once: true });
  }

  if (still) {
    film.removeAttribute('autoplay');
    film.loop = false;
    whenReady(park);
    film.pause();
    return;
  }

  whenReady(function () {
    var p;
    try { p = film.play(); } catch (e) {}
    if (p && p.catch) p.catch(park);
    // A resolved play() promise is not proof it is running — a background tab
    // reports exactly that while staying paused. Check the clock instead.
    setTimeout(function () {
      if (film.paused && !film.currentTime) park();
    }, 1200);
  });

  // ...and pick it up again when the tab comes back to the front
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && film.paused) { try { film.play(); } catch (e) {} }
  });
})();

// Widget Configurator — the prototype runs live in an iframe, scaled to the
// panel. It only loads and only runs while the section is on screen.
(function () {
  var box = document.getElementById('configurator');
  var frame = document.getElementById('configuratorFrame');
  if (!box || !frame) return;
  var BASE_W = 1211, BASE_H = 581;
  var narrow = window.matchMedia && matchMedia('(max-width: 700px)');
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var started = false;

  function fit() {
    var byW = box.clientWidth / BASE_W;
    // on a phone the proportional scale is unreadable, so fill the taller box
    // and let it crop from the right — the config column stays legible
    var k = (narrow && narrow.matches) ? Math.max(byW, box.clientHeight / BASE_H) : byW;
    frame.style.transform = 'scale(' + k + ')';
  }
  fit();
  if (window.ResizeObserver) new ResizeObserver(fit).observe(box);
  else window.addEventListener('resize', fit);

  function inner() {
    try { return frame.contentWindow; } catch (e) { return null; }
  }

  function enter() {
    box.classList.add('is-live');          // pulls in the plate artwork
    if (!frame.getAttribute('src')) {
      frame.setAttribute('src', frame.dataset.src);
      frame.addEventListener('load', function () { fit(); if (!still) start(); });
      return;
    }
    if (!still) start();
  }
  function start() {
    var w = inner();
    if (!w) return;
    if (!started && typeof w.__startSegment === 'function') { started = true; w.__startSegment(); }
    else if (typeof w.play === 'function') w.play();
  }
  function leave() {
    var w = inner();
    if (w && typeof w.pause === 'function') w.pause();
  }

  if (window.IntersectionObserver) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { e.isIntersecting ? enter() : leave(); });
    }, { threshold: 0.15, rootMargin: '200px 0px' }).observe(box);
  } else {
    enter();
  }
})();

// FAQ accordion — one answer open at a time, as on availproject.org: opening
// a question closes whichever was open, and clicking the open one closes it.
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('.faq__item'));

  function set(item, open) {
    item.dataset.open = String(open);
    item.querySelector('.faq__q').setAttribute('aria-expanded', String(open));
  }

  items.forEach(function (item) {
    item.querySelector('.faq__q').addEventListener('click', function () {
      var wasOpen = item.dataset.open === 'true';
      items.forEach(function (i) { set(i, false); });
      if (!wasOpen) set(item, true);
    });
  });
})();
