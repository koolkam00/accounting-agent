/*
  site.js: forms and visit counts. Loaded with "defer". No copy lives here.

  Forms
  - Field names are the sheet column names (CONTRACTS.md section 6.3). Helper controls start
    with "ui_" and are never sent. The server (apps-script/Code.gs) validates everything again.
  - With FORM_ENDPOINT empty (staging), a valid form shows "Staging: submissions are not live
    yet" and sends nothing. It never shows the thank-you message unless the server said ok.
  - The submit buttons ship disabled in the HTML, so a browser without JavaScript cannot send a
    form (it would otherwise put the answers in the address bar). setup() enables each one last.

  Visit counts (GoatCounter, no cookies): a page view on load, and the events
  "<form>-intake-started" and "<form>-intake-sent". Off when ANALYTICS.ENDPOINT is empty, and
  for visitors with Do Not Track or Global Privacy Control on.
*/
(function () {
  "use strict";
  var C = window.SITE_CONFIG || {};
  var A = C.ANALYTICS || {};
  var page = document.documentElement.getAttribute("data-page") || "";

  /* ---------- nav: mark the current page ---------- */
  var links = document.querySelectorAll(".site-nav a");
  for (var i = 0; i < links.length; i++) {
    if (links[i].getAttribute("href") === page + ".html") links[i].setAttribute("aria-current", "page");
  }

  /* ---------- visit counts ---------- */
  var privacyOff = A.RESPECT_DO_NOT_TRACK !== false &&
    (navigator.doNotTrack === "1" || window.doNotTrack === "1" || navigator.globalPrivacyControl === true);
  var countOn = !!(A.ENDPOINT && /^https?:\/\//.test(A.ENDPOINT) && !privacyOff);

  function count(path, isEvent) {
    if (!countOn) return;
    var q = ["p=" + encodeURIComponent(path), "t=" + encodeURIComponent(document.title)];
    if (isEvent) q.push("e=true");
    else {
      if (document.referrer) q.push("r=" + encodeURIComponent(document.referrer));
      if (location.search) q.push("q=" + encodeURIComponent(location.search)); // campaign tags such as ?utm_campaign=...
      q.push("s=" + [screen.width, screen.height, window.devicePixelRatio || 1].join(","));
    }
    if (navigator.webdriver) q.push("b=153"); // GoatCounter's flag for automated browsers
    q.push("rnd=" + Math.random().toString(36).slice(2, 8));
    var img = new Image();
    img.src = A.ENDPOINT + "?" + q.join("&");
  }
  window.siteCount = count;
  count(page === "index" ? "/" : "/" + page, false);

  /* ---------- forms ---------- */
  var MSG = {
    required: "Please fill this in.",
    choose: "Please choose one.",
    pick: "Pick at least one category, or choose \"Any of them\".",
    confirm: "Please confirm this to continue.",
    email: "Enter an email address like name@company.com.",
    url: "Enter a web address like yourbrand.com.",
    int: "Enter a number, like 60.",
    phone: "Enter a phone number. Digits, spaces and dashes are fine.",
    too_long: "This is too long. Please shorten it.",
    invalid: "Please check this answer."
  };
  var ALL_CATEGORIES = ["chips-crisps", "popcorn-puffs", "crackers-pretzels", "bars", "cookies-baked", "chocolate-candy",
    "nuts-seeds-trail", "meat-snacks", "fruit-snacks", "sparkling-soda", "tea-juice", "coffee-rtd", "other-snack", "other-drink"];

  function contactText() {
    var e = C.CONTACT_EMAIL || "[EMAIL]";
    return e;
  }

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "x" + Date.now().toString(36) + Math.random().toString(36).slice(2, 12);
  }

  function setup(form) {
    var kind = form.getAttribute("data-form");
    var section = form.closest("section");
    var summary = form.querySelector(".error-summary");
    var status = form.querySelector(".form-status");
    var done = section.querySelector(".form-done");
    var button = form.querySelector('button[type="submit"]');
    var staging = section.querySelector("[data-staging-form]");
    var live = !!(C.FORM_ENDPOINT && /^https:\/\/|^http:\/\/(localhost|127\.0\.0\.1)/.test(C.FORM_ENDPOINT));
    var submissionId = uuid();
    var started = false;
    var sending = false;

    if (!live && staging) staging.classList.add("is-shown");

    // Conditional fields: data-show-if="name=value"
    var reveals = form.querySelectorAll("[data-show-if]");
    function valueOf(name) {
      var els = form.elements[name];
      if (!els) return "";
      if (els.length !== undefined && !els.tagName) {
        for (var j = 0; j < els.length; j++) if (els[j].checked) return els[j].value;
        return "";
      }
      if (els.type === "checkbox" || els.type === "radio") return els.checked ? els.value : "";
      return els.value;
    }
    function updateReveals() {
      for (var j = 0; j < reveals.length; j++) {
        var rule = reveals[j].getAttribute("data-show-if").split("=");
        reveals[j].hidden = valueOf(rule[0]) !== rule[1];
      }
    }
    form.addEventListener("change", updateReveals);
    updateReveals();

    form.addEventListener("input", function () {
      if (!started) { started = true; count(kind + "-intake-started", true); }
    });

    // Size notes (review round 3, R3-04): a gentle, non-blocking line when a number is outside
    // the range the page states, for example an office under 30 or over 250 people.
    var sizeNotes = form.querySelectorAll("[data-size-note]");
    function updateSizeNotes() {
      for (var j = 0; j < sizeNotes.length; j++) {
        var note = sizeNotes[j], el = form.elements[note.getAttribute("data-size-note")];
        var n = el ? parseInt(String(el.value).replace(/[\s,]/g, ""), 10) : NaN;
        var out = !isNaN(n) && n >= 1 && (n < +note.getAttribute("data-min") || n > +note.getAttribute("data-max"));
        var text = out ? "Offices this size can't join yet. You can still send the form, and we will reply." : "";
        if (note.textContent !== text) note.textContent = text;
      }
    }
    form.addEventListener("input", updateSizeNotes);
    updateSizeNotes();

    function visible(el) { return !el.closest("[hidden]"); }

    function errTarget(name) {
      var holder = form.querySelector('[data-name="' + name + '"]');
      if (holder) return holder;
      return form.elements[name] && form.elements[name].tagName ? form.elements[name] : null;
    }
    function labelFor(name) {
      var holder = form.querySelector('[data-name="' + name + '"]');
      if (holder) { var lg = holder.querySelector("legend"); return (lg.innerText || lg.textContent).replace(/\s+/g, " ").trim(); }
      var el = form.elements[name];
      var lab = el && el.id ? form.querySelector('label[for="' + el.id + '"]') : null;
      return lab ? lab.textContent.replace(/\(optional\)/, "").trim() : name;
    }
    function focusTarget(name) {
      var holder = form.querySelector('[data-name="' + name + '"]');
      if (holder) {
        var first = holder.querySelector("input:checked") || holder.querySelector("input");
        return first;
      }
      return form.elements[name];
    }

    function clearErrors() {
      var errs = form.querySelectorAll(".err");
      for (var j = 0; j < errs.length; j++) errs[j].textContent = "";
      var inv = form.querySelectorAll('[aria-invalid="true"]');
      for (var k = 0; k < inv.length; k++) inv[k].removeAttribute("aria-invalid");
      var he = form.querySelectorAll(".has-error");
      for (var m = 0; m < he.length; m++) he[m].classList.remove("has-error");
      summary.hidden = true;
      summary.querySelector("ul").innerHTML = "";
    }

    function showErrors(errors) {
      var names = Object.keys(errors).filter(function (n) { return errTarget(n); });
      if (!names.length) return;
      // List problems in the order they appear on the page.
      names.sort(function (x, y) {
        return errTarget(x).compareDocumentPosition(errTarget(y)) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
      });
      var ul = summary.querySelector("ul");
      names.forEach(function (name) {
        var target = errTarget(name);
        if (!target) return;
        var errEl = form.querySelector("#" + target.id + "-err");
        if (errEl) errEl.textContent = errors[name];
        if (target.tagName === "FIELDSET") target.classList.add("has-error");
        else target.setAttribute("aria-invalid", "true");
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = "#" + (focusTarget(name).id || target.id);
        var lab = labelFor(name);
        a.textContent = lab + (/[?.:]$/.test(lab) ? " " : ": ") + errors[name];
        a.addEventListener("click", function (ev) {
          ev.preventDefault();
          var f = focusTarget(name);
          if (f) { f.focus(); f.scrollIntoView({ block: "center" }); }
        });
        li.appendChild(a);
        ul.appendChild(li);
      });
      summary.hidden = false;
      summary.focus();
    }

    // Client-side checks mirror apps-script/Code.gs. The server checks again.
    function collect() {
      var errors = {};
      var data = {};
      var seen = {};
      var els = form.elements;
      for (var j = 0; j < els.length; j++) {
        var el = els[j];
        var name = el.name;
        if (!name || seen[name] || el.type === "submit") continue;
        seen[name] = true;
        if (name === "hp_url") { data.hp_url = el.value; continue; }
        var holder = form.querySelector('[data-name="' + name + '"]');
        var shown = visible(el);
        if (el.type === "radio") {
          var v = valueOf(name);
          if (name.indexOf("ui_") !== 0) data[name] = v;
          if (!v && el.required && shown) errors[holder ? holder.getAttribute("data-name") : name] = MSG.choose;
          continue;
        }
        if (el.type === "checkbox") {
          if (name === "categories_wanted") continue; // handled below
          data[name] = el.checked ? el.value : "";
          if (!el.checked && el.required) errors[name] = MSG.confirm;
          continue;
        }
        var val = (el.value || "").trim();
        if (name.indexOf("ui_") !== 0) data[name] = shown ? val : "";
        var reqIf = el.getAttribute("data-required-if");
        var needed = el.required || (reqIf && shown && valueOf(reqIf.split("=")[0]) === reqIf.split("=")[1]);
        if (!val) { if (needed) errors[name] = MSG.required; continue; }
        var max = parseInt(el.getAttribute("maxlength") || "0", 10);
        if (max && val.length > max) { errors[name] = MSG.too_long; continue; }
        var type = el.getAttribute("data-type") || el.type;
        if (type === "email" && !/^[^\s@<>()",;:]+@[^\s@<>()",;:]+\.[A-Za-z]{2,}$/.test(val)) errors[name] = MSG.email;
        else if (type === "url" && (/\s/.test(val) || !/^(https?:\/\/)?[^\/\s.]+\.[^\s]{2,}$/i.test(val))) errors[name] = MSG.url;
        else if (type === "int") {
          var digits = val.replace(/[,\s]/g, "");
          if (!/^\d{1,6}$/.test(digits) || +digits < 1 || +digits > 10000) errors[name] = MSG.int;
          else data[name] = digits;
        } else if (type === "phone" && !/^[0-9+().\-\s/x#ext]{7,40}$/i.test(val)) errors[name] = MSG.phone;
      }

      // Office: compose the receiving window and the category list.
      if (kind === "office") {
        var w = valueOf("ui_receiving_window");
        data.receiving_window = w === "other" ? (form.elements.ui_receiving_window_other.value || "").trim() : w;
        if (errors.ui_receiving_window_other) { errors.receiving_window = errors.ui_receiving_window_other; delete errors.ui_receiving_window_other; }
        if (errors.ui_receiving_window) { errors.receiving_window = errors.ui_receiving_window; delete errors.ui_receiving_window; }
        if (valueOf("ui_categories_mode") === "some") {
          var picked = [];
          var boxes = form.querySelectorAll('input[name="categories_wanted"]');
          for (var b = 0; b < boxes.length; b++) if (boxes[b].checked) picked.push(boxes[b].value);
          if (!picked.length) errors.categories_wanted = MSG.pick;
          data.categories_wanted = picked.join(";");
        } else {
          data.categories_wanted = ALL_CATEGORIES.join(";");
        }
      }
      return { data: data, errors: errors };
    }

    function say(text, alert) {
      status.textContent = text;
      status.classList.toggle("is-alert", !!alert);
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (sending) return;
      clearErrors();
      say("", false);
      var r = collect();
      if (Object.keys(r.errors).length) { showErrors(r.errors); return; }

      if (!live) {
        say("Staging: submissions are not live yet. Nothing was sent. To reach us now, email " + contactText() + ".", true);
        return;
      }

      var body = new URLSearchParams();
      body.set("form", kind);
      // Question 6 asks about $1,500 instead of $600 once the founding tier is closed; that form
      // has its own version so the sheet shows which amount was asked (HANDOFF.md).
      var fv = C.FORM_VERSION || {};
      var version = (kind === "brand" && C.FOUNDING_TIER_OPEN === false && fv.brand_standard_only) || fv[kind];
      body.set("form_version", version || kind + "-unknown");
      body.set("submission_id", submissionId);
      Object.keys(r.data).forEach(function (k) { body.set(k, r.data[k]); });

      sending = true;
      button.disabled = true;
      say("Sending…", false);
      var ctrl = window.AbortController ? new AbortController() : null;
      var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 20000);
      fetch(C.FORM_ENDPOINT, { method: "POST", body: body, redirect: "follow", signal: ctrl ? ctrl.signal : undefined })
        .then(function (res) { return res.json(); })
        .then(function (json) {
          if (json && json.ok === true) {
            form.hidden = true;
            done.hidden = false;
            done.focus();
            count(kind + "-intake-sent", true);
            return;
          }
          if (json && json.error === "validation" && json.fields) {
            var errs = {};
            Object.keys(json.fields).forEach(function (k) {
              var code = json.fields[k];
              var key = k === "receiving_window" ? "receiving_window" : k;
              errs[key] = MSG[code] || MSG.invalid;
            });
            say("", false);
            showErrors(errs);
            return;
          }
          if (json && json.error === "busy") {
            say("Too many submissions right now. Please try again in a few minutes, or email " + contactText() + ".", true);
            return;
          }
          throw new Error("unexpected response");
        })
        .catch(function () {
          say("We could not confirm that your answers were sent. Please try again in a minute, or email " + contactText() + ".", true);
        })
        .then(function () {
          clearTimeout(timer);
          sending = false;
          button.disabled = false;
        });
    });

    button.disabled = false; // last: the form is ready to send
  }

  var forms = document.querySelectorAll("form[data-form]");
  for (var f = 0; f < forms.length; f++) setup(forms[f]);
})();
