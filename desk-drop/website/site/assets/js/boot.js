/*
  boot.js: runs in <head>, right after site.config.js, before the page paints.
  Do not edit for copy changes; edit site.config.js instead.

  1. Reads window.SITE_CONFIG (fails safe: staging on, forms off, if the config is missing).
  2. Sets classes on <html>: js, is-staging, founding-closed.
  3. Robots: every page ships with <meta name="robots" content="noindex, nofollow"> in its HTML,
     so it holds without JavaScript. This removes it only when STAGING is false. (The production
     copy written by tools/make_production.py has it removed already.)
  4. Fills every element marked data-config="KEY" with that config value, as the parser
     creates it. A MutationObserver callback runs before the browser's next paint, so the
     name never pops in late and nothing shifts. data-config-mailto, data-config-tel and
     data-config-url also set the link; data-config-line="KEY" hides a whole line when KEY is "".
     tools/make_production.py writes the same values into the HTML, for visitors and link
     previews that do not run JavaScript.
*/
(function () {
  "use strict";
  var C = window.SITE_CONFIG || {};
  var SAFE = { STAGING: true, FORM_ENDPOINT: "", FOUNDING_TIER_OPEN: true, ANALYTICS: { ENDPOINT: "" } };
  for (var k in SAFE) if (!(k in C)) C[k] = SAFE[k];
  window.SITE_CONFIG = C;

  var root = document.documentElement;
  root.classList.add("js");
  if (C.STAGING !== false) root.classList.add("is-staging");
  if (C.FOUNDING_TIER_OPEN === false) root.classList.add("founding-closed");

  var isPlaceholder = function (v) { return typeof v === "string" && /^\[[^\]]+\]$/.test(v.trim()); };
  window.SITE_IS_PLACEHOLDER = isPlaceholder;

  function addMeta(attr, key, content) {
    var m = document.createElement("meta");
    m.setAttribute(attr, key);
    m.setAttribute("content", content);
    document.head.appendChild(m);
  }

  var robots = document.querySelectorAll('meta[name="robots"]');
  if (C.STAGING === false) {
    for (var r = 0; r < robots.length; r++) robots[r].parentNode.removeChild(robots[r]);
  } else if (!robots.length) {
    addMeta("name", "robots", "noindex, nofollow");
  }

  // Canonical URL and og:url only once a real domain is set. Extension-less, because
  // Cloudflare Pages redirects /brands.html to /brands (SETUP.md section 12).
  var page = root.getAttribute("data-page") || "";
  if (C.DOMAIN && !isPlaceholder(C.DOMAIN) && page !== "404" && !document.querySelector('link[rel="canonical"]')) {
    var file = page === "index" ? "" : page;
    var url = "https://" + C.DOMAIN.replace(/^https?:\/\//, "").replace(/\/$/, "") + "/" + file;
    var l = document.createElement("link");
    l.rel = "canonical"; l.href = url; document.head.appendChild(l);
    addMeta("property", "og:url", url);
  }
  if (C.BRAND_NAME) {
    if (!document.querySelector('meta[property="og:site_name"]')) addMeta("property", "og:site_name", C.BRAND_NAME);
    if (document.title.indexOf(C.BRAND_NAME) === -1) document.title = document.title + " · " + C.BRAND_NAME;
  }

  function fill(el) {
    var key = el.getAttribute("data-config");
    if (!key || !(key in C)) return;
    var v = String(C[key]);
    if (el.textContent !== v) el.textContent = v;
    var ph = isPlaceholder(v);
    el.classList.toggle("is-placeholder", ph);
    if (el.hasAttribute("data-config-mailto")) {
      if (ph) el.removeAttribute("href"); else el.setAttribute("href", "mailto:" + v);
    }
    if (el.hasAttribute("data-config-tel")) {
      if (ph) el.removeAttribute("href"); else el.setAttribute("href", "tel:" + v.replace(/[^0-9+]/g, ""));
    }
    if (el.hasAttribute("data-config-url")) {
      if (ph || !/^https:\/\//.test(v)) el.removeAttribute("href"); else el.setAttribute("href", v);
      if (!ph) el.textContent = v.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "");
    }
  }
  function line(el) {
    var key = el.getAttribute("data-config-line");
    if (key in C) el.hidden = String(C[key]).trim() === "";
  }
  function scan(node) {
    if (node.nodeType !== 1) return;
    if (node.hasAttribute("data-config")) fill(node);
    if (node.hasAttribute("data-config-line")) line(node);
    var list = node.querySelectorAll("[data-config]");
    for (var i = 0; i < list.length; i++) fill(list[i]);
    var lines = node.querySelectorAll("[data-config-line]");
    for (var j = 0; j < lines.length; j++) line(lines[j]);
  }

  var mo = new MutationObserver(function (records) {
    for (var i = 0; i < records.length; i++) {
      var added = records[i].addedNodes;
      for (var j = 0; j < added.length; j++) scan(added[j]);
    }
  });
  mo.observe(root, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", function () {
    mo.disconnect();
    scan(document.body); // final pass, in case anything was missed
  });
})();
