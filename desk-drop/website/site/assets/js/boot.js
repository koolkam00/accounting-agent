/*
  boot.js: runs in <head>, right after site.config.js, before the page paints.
  Do not edit for copy changes; edit site.config.js instead.

  1. Reads window.SITE_CONFIG (fails safe: staging on, forms off, if the config is missing).
  2. Sets classes on <html>: js, is-staging, founding-closed.
  3. Adds <meta name="robots" content="noindex, nofollow"> while STAGING is true.
  4. Fills every element marked data-config="KEY" with that config value, as the parser
     creates it. A MutationObserver callback runs before the browser's next paint, so the
     name never pops in late and nothing shifts.
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

  if (C.STAGING !== false) addMeta("name", "robots", "noindex, nofollow");

  // Canonical URL and og:url only once a real domain is set.
  var page = root.getAttribute("data-page") || "";
  if (C.DOMAIN && !isPlaceholder(C.DOMAIN)) {
    var file = page === "index" ? "" : page + ".html";
    var url = "https://" + C.DOMAIN.replace(/^https?:\/\//, "").replace(/\/$/, "") + "/" + file;
    var l = document.createElement("link");
    l.rel = "canonical"; l.href = url; document.head.appendChild(l);
    addMeta("property", "og:url", url);
  }
  if (C.BRAND_NAME) {
    addMeta("property", "og:site_name", C.BRAND_NAME);
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
  }
  function scan(node) {
    if (node.nodeType !== 1) return;
    if (node.hasAttribute("data-config")) fill(node);
    var list = node.querySelectorAll("[data-config]");
    for (var i = 0; i < list.length; i++) fill(list[i]);
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
