/* ============================================================
   Road Network Integration Toolkit — site interactions
   Vanilla JS. No dependencies.
   ============================================================ */
(function () {
  "use strict";

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ----------------------------------------------------------
     Header: scroll state, progress bar, active section
     ---------------------------------------------------------- */
  var header = document.getElementById("siteHeader");
  var progress = document.getElementById("scrollProgress");

  function onScroll() {
    var y = window.scrollY || window.pageYOffset;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (header) header.classList.toggle("is-scrolled", y > 8);
    if (progress) progress.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  onScroll();

  /* ----------------------------------------------------------
     Mobile navigation
     ---------------------------------------------------------- */
  var navToggle = document.getElementById("navToggle");
  var nav = document.getElementById("primaryNav");

  function closeNav() {
    if (!nav || !navToggle) return;
    nav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "Open navigation");
  }

  function openNav() {
    nav.classList.add("is-open");
    navToggle.setAttribute("aria-expanded", "true");
    navToggle.setAttribute("aria-label", "Close navigation");
  }

  if (navToggle && nav) {
    navToggle.addEventListener("click", function () {
      if (nav.classList.contains("is-open")) closeNav();
      else openNav();
    });

    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) closeNav();
    });

    document.addEventListener("click", function (e) {
      if (!nav.classList.contains("is-open")) return;
      if (!nav.contains(e.target) && !navToggle.contains(e.target)) closeNav();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        closeNav();
        navToggle.focus();
      }
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 980) closeNav();
    });
  }

  /* ----------------------------------------------------------
     Active nav link
     ---------------------------------------------------------- */
  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".nav a[href^='#']"));
  var navSections = navLinks
    .map(function (link) {
      var id = link.getAttribute("href").slice(1);
      return document.getElementById(id);
    })
    .filter(Boolean);

  if ("IntersectionObserver" in window && navSections.length) {
    var navObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var id = entry.target.id;
          navLinks.forEach(function (link) {
            link.classList.toggle("is-active", link.getAttribute("href") === "#" + id);
          });
        });
      },
      { rootMargin: "-42% 0px -50% 0px", threshold: 0 }
    );
    navSections.forEach(function (section) { navObserver.observe(section); });
  }

  /* ----------------------------------------------------------
     Scroll reveals
     ---------------------------------------------------------- */
  var revealItems = Array.prototype.slice.call(document.querySelectorAll("[data-reveal]"));
  if ("IntersectionObserver" in window && !reducedMotion) {
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    revealItems.forEach(function (item) { revealObserver.observe(item); });
  } else {
    revealItems.forEach(function (item) { item.classList.add("is-visible"); });
  }

  /* ----------------------------------------------------------
     Stat counters
     ---------------------------------------------------------- */
  var counters = Array.prototype.slice.call(document.querySelectorAll("[data-count]"));
  if (counters.length && !reducedMotion && "IntersectionObserver" in window) {
    var counterObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var target = parseInt(el.getAttribute("data-count"), 10) || 0;
          var start = null;
          var duration = 1100;

          function step(ts) {
            if (start === null) start = ts;
            var p = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * eased).toString();
            if (p < 1) requestAnimationFrame(step);
          }
          requestAnimationFrame(step);
          counterObserver.unobserve(el);
        });
      },
      { threshold: 0.6 }
    );
    counters.forEach(function (c) { counterObserver.observe(c); });
  }

  /* ----------------------------------------------------------
     Hero map layer toggles
     ---------------------------------------------------------- */
  var layerButtons = Array.prototype.slice.call(document.querySelectorAll(".layer-toggle"));
  layerButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var layer = btn.getAttribute("data-layer");
      var target = document.querySelector(".map-layer.layer-" + layer);
      var pressed = btn.getAttribute("aria-pressed") === "true";
      btn.setAttribute("aria-pressed", String(!pressed));
      btn.classList.toggle("is-on", !pressed);
      if (target) target.classList.toggle("is-hidden", pressed);
    });
  });

  /* ----------------------------------------------------------
     Method tabs (WAI-ARIA tabs pattern)
     ---------------------------------------------------------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".method-tab"));
  var panels = Array.prototype.slice.call(document.querySelectorAll(".method-panel"));

  function selectTab(tab, focus) {
    var targetId = tab.getAttribute("aria-controls");
    tabs.forEach(function (t) {
      var selected = t === tab;
      t.classList.toggle("is-active", selected);
      t.setAttribute("aria-selected", String(selected));
      t.setAttribute("tabindex", selected ? "0" : "-1");
    });
    panels.forEach(function (panel) {
      var selected = panel.id === targetId;
      panel.hidden = !selected;
      panel.classList.toggle("is-active", selected);
    });
    if (focus) tab.focus();
  }

  tabs.forEach(function (tab, index) {
    tab.addEventListener("click", function () { selectTab(tab, false); });
    tab.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") next = tabs[(index + 1) % tabs.length];
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = tabs[(index - 1 + tabs.length) % tabs.length];
      if (e.key === "Home") next = tabs[0];
      if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) {
        e.preventDefault();
        selectTab(next, true);
      }
    });
  });

  /* ----------------------------------------------------------
     Coverage explorer
     ---------------------------------------------------------- */
  var range = document.getElementById("coverageRange");
  var coverageValue = document.getElementById("coverageValue");
  var ratioValue = document.getElementById("ratioValue");
  var className = document.getElementById("className");
  var classAdded = document.getElementById("classAdded");
  var classBadge = document.getElementById("classBadge");
  var roadCovered = document.getElementById("roadCovered");
  var roadRemaining = document.getElementById("roadRemaining");
  var roadMarker = document.getElementById("roadMarker");
  var tableRows = Array.prototype.slice.call(document.querySelectorAll(".class-table tbody tr"));

  function classify(ratio) {
    // Mirrors the legacy thresholds, including the intentional gap at 0.25.
    if (ratio <= 0.01) return { name: "missing_a", added: false, status: "stop" };
    if (ratio < 0.25) return { name: "missing_b", added: false, status: "stop" };
    if (ratio === 0.25) return { name: "unclassified", added: false, status: "gap" };
    if (ratio <= 0.5) return { name: "missing_4", added: true, status: "go" };
    if (ratio <= 0.75) return { name: "missing_3", added: true, status: "go" };
    if (ratio < 1) return { name: "missing_2", added: true, status: "go" };
    return { name: "missing_1", added: true, status: "go" };
  }

  function updateCoverage() {
    if (!range) return;
    var coverage = parseFloat(range.value);
    var ratio = Math.round((1 - coverage / 100) * 100) / 100;
    var result = classify(ratio);

    if (coverageValue) coverageValue.textContent = coverage + "%";
    if (ratioValue) ratioValue.textContent = ratio.toFixed(2);
    if (className) className.textContent = result.name;
    if (classAdded) {
      classAdded.textContent = result.added ? "Yes" : "No";
      classAdded.classList.toggle("yes", result.added);
      classAdded.classList.toggle("no", !result.added);
    }
    if (classBadge) {
      classBadge.textContent = result.name;
      classBadge.classList.toggle("is-stop", result.status === "stop");
      classBadge.classList.toggle("is-gap", result.status === "gap");
    }
    if (roadCovered) roadCovered.style.width = coverage + "%";
    if (roadRemaining) roadRemaining.style.width = (100 - coverage) + "%";
    if (roadMarker) roadMarker.style.left = coverage + "%";

    tableRows.forEach(function (row) {
      row.classList.toggle("is-active", row.getAttribute("data-class") === result.name);
    });
  }

  if (range) {
    range.addEventListener("input", updateCoverage);
    updateCoverage();
  }

  /* ----------------------------------------------------------
     Illustrative processing console
     ---------------------------------------------------------- */
  var consoleBody = document.getElementById("consoleBody");
  if (consoleBody) {
    var lines = Array.prototype.slice.call(consoleBody.querySelectorAll(".cl"));
    var started = false;

    function playConsole() {
      if (started || reducedMotion) return;
      started = true;
      var index = 0;

      lines.forEach(function (line) { line.style.opacity = "0.18"; });

      function revealNext() {
        if (index >= lines.length) {
          window.setTimeout(function () {
            lines.forEach(function (line) { line.style.opacity = "0.18"; });
            index = 0;
            window.setTimeout(revealNext, 600);
          }, 3600);
          return;
        }
        var line = lines[index];
        line.style.opacity = "1";
        line.classList.add("is-new");
        window.setTimeout(function () { line.classList.remove("is-new"); }, 400);
        index += 1;
        window.setTimeout(revealNext, 620);
      }
      revealNext();
    }

    if ("IntersectionObserver" in window) {
      var consoleObserver = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              playConsole();
              consoleObserver.disconnect();
            }
          });
        },
        { threshold: 0.35 }
      );
      consoleObserver.observe(consoleBody);
    } else {
      playConsole();
    }
  }

  /* ----------------------------------------------------------
     Pointer glow on bento cards
     ---------------------------------------------------------- */
  if (!reducedMotion && window.matchMedia("(pointer: fine)").matches) {
    Array.prototype.forEach.call(document.querySelectorAll(".card"), function (card) {
      card.addEventListener("pointermove", function (e) {
        var rect = card.getBoundingClientRect();
        card.style.setProperty("--mx", ((e.clientX - rect.left) / rect.width) * 100 + "%");
        card.style.setProperty("--my", ((e.clientY - rect.top) / rect.height) * 100 + "%");
      });
    });
  }

  /* ----------------------------------------------------------
     Year
     ---------------------------------------------------------- */
  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
