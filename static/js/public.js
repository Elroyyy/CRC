"use strict";

const pages = [...document.querySelectorAll(".page")];
const menuButton = document.querySelector(".hamburger");
const sidebar = document.querySelector(".sidebar");
const overlay = document.querySelector(".sidebar-overlay");
const mobile = matchMedia("(max-width: 700px)");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");

function closeMenu(restoreFocus = false) {
  sidebar.classList.remove("active");
  overlay.classList.remove("active");
  document.body.classList.remove("menu-open");
  menuButton.setAttribute("aria-expanded", "false");
  menuButton.setAttribute("aria-label", "Open menu");
  if (restoreFocus) menuButton.focus();
}

menuButton.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") !== "true";
  closeMenu();
  if (!open) return;
  sidebar.classList.add("active");
  overlay.classList.add("active");
  document.body.classList.add("menu-open");
  menuButton.setAttribute("aria-expanded", "true");
  menuButton.setAttribute("aria-label", "Close menu");
  sidebar.querySelector("a").focus();
});
overlay.addEventListener("click", () => closeMenu(true));
mobile.addEventListener("change", () => closeMenu());
document.addEventListener("keydown", (event) => {
  if (menuButton.getAttribute("aria-expanded") !== "true") return;
  if (event.key === "Escape") closeMenu(true);
  if (event.key !== "Tab") return;
  const items = [menuButton, ...sidebar.querySelectorAll("a")];
  const current = items.indexOf(document.activeElement);
  if (event.shiftKey && current === 0) {
    event.preventDefault();
    items.at(-1).focus();
  } else if (!event.shiftKey && current === items.length - 1) {
    event.preventDefault();
    menuButton.focus();
  }
});

function renderLocation(focus = false) {
  const id = location.pathname.replace(/^\//, "") || "home";
  const page = document.getElementById(id) || document.getElementById("home");
  pages.forEach((item) => {
    const active = item === page;
    item.classList.toggle("active", active);
    item.setAttribute("aria-hidden", String(!active));
    if (active) item.setAttribute("role", "main");
    else item.removeAttribute("role");
  });
  page.tabIndex = -1;
  document.querySelector(".skip-link").href = `#${page.id}`;
  document.querySelectorAll("[data-page], [data-contact]").forEach((link) => {
    const active = link.hasAttribute("data-contact")
      ? location.hash === "#contact-section"
      : link.dataset.page === page.id && !location.hash;
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  closeMenu();
  const target =
    location.hash === "#contact-section"
      ? document.getElementById("contact-section")
      : page;
  const heading = target.querySelector("h1, h2");
  document.title = `${page.id === "home" ? "Dehiwala Community Church" : heading?.textContent || "Church"} | DCC`;
  if (focus && heading) {
    heading.tabIndex = -1;
    heading.focus({ preventScroll: true });
  }
  window.dispatchEvent(new Event("dcc:route-change"));
  return target;
}

document
  .querySelectorAll("[data-page], [data-contact], .logo")
  .forEach((link) => {
    link.addEventListener("click", (event) => {
      if (
        event.button ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        event.altKey
      )
        return;
      event.preventDefault();
      history.replaceState({ y: scrollY }, "", location.href);
      history.pushState({ y: 0 }, "", link.href);
      const target = renderLocation(true);
      // One scroll operation, with no scroll listener or wheel interception.
      if (location.hash) {
        target.scrollIntoView({
          behavior: reducedMotion.matches ? "auto" : "smooth",
        });
      } else {
        window.scrollTo({ top: 0, behavior: "instant" });
      }
    });
  });
history.scrollRestoration = "manual";
window.addEventListener("popstate", (event) => {
  renderLocation(true);
  window.scrollTo({ top: event.state?.y || 0, behavior: "instant" });
});
const initialTarget = renderLocation();
if (location.hash) requestAnimationFrame(() => initialTarget.scrollIntoView());

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function renderEvents(events, container, limit) {
  container.replaceChildren();
  container.setAttribute("aria-busy", "false");
  if (!events.length) {
    container.append(
      node(
        "p",
        "There are no church events to display at the moment.",
        "event-state",
      ),
    );
    return;
  }
  events.slice(0, limit).forEach((event) => {
    const card = node("article", "", "event-card");
    if (event.image_path) {
      try {
        const source = event.image_path.startsWith("uploads/")
          ? `/static/${event.image_path}`
          : event.image_path;
        const url = new URL(source, location.origin);
        if (url.protocol === "https:" || url.origin === location.origin) {
          const image = node("img");
          image.src = url.href;
          image.alt = `${event.title || "Church event"} poster`;
          image.loading = "lazy";
          image.addEventListener("error", () =>
            image.replaceWith(node("p", "Event photograph unavailable.")),
          );
          card.append(image);
        }
      } catch {
        /* Event text remains available if its image URL is invalid. */
      }
    }
    const date = new Date(`${String(event.event_date).slice(0, 10)}T00:00:00`);
    const meta = node("div", "", "event-meta");
    if (!Number.isNaN(date.getTime())) {
      const time = node(
        "time",
        date.toLocaleDateString("en-GB", {
          day: "numeric",
          month: "long",
          year: "numeric",
        }),
      );
      time.dateTime = String(event.event_date).slice(0, 10);
      meta.append(time);
    }
    card.append(
      meta,
      node("h3", event.title || "Church event"),
      node("p", event.description || ""),
    );
    container.append(card);
  });
}

async function loadEvents() {
  const containers = [
    document.getElementById("home-events"),
    document.getElementById("all-events"),
  ];
  containers.forEach((container) => {
    container.setAttribute("aria-busy", "true");
    container.replaceChildren(
      node("p", "Loading church events…", "event-state"),
    );
  });
  try {
    const response = await fetch("/api/events", {
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) throw new Error("Events unavailable");
    const events = await response.json();
    if (!Array.isArray(events)) throw new Error("Invalid events");
    events.sort((a, b) =>
      String(b.event_date).localeCompare(String(a.event_date)),
    );
    renderEvents(events, containers[0], 3);
    renderEvents(events, containers[1], events.length);
  } catch {
    containers.forEach((container) => {
      const state = node("div", "", "event-state");
      const retry = node("button", "Try again");
      retry.type = "button";
      retry.addEventListener("click", loadEvents);
      state.append(
        node("p", "Church events could not be loaded. Please try again."),
        retry,
      );
      container.replaceChildren(state);
      container.setAttribute("aria-busy", "false");
    });
  }
}
loadEvents();

document
  .querySelectorAll("[data-inquiry-form], [data-rental-form]")
  .forEach((form) => {
    const rental = form.hasAttribute("data-rental-form");
    const limits = {
      name: 120,
      phone: 40,
      email: 254,
      note: 3000,
      message: 3000,
    };
    Object.entries(limits).forEach(([name, length]) => {
      if (form.elements[name]) form.elements[name].maxLength = length;
    });
    ["name", "email", "phone"].forEach((name) => {
      form.elements[name].autocomplete = name === "phone" ? "tel" : name;
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector('[type="submit"]');
      if (button.disabled) return;
      const status = form.querySelector(".form-status");
      const data = new FormData(form);
      const payload = Object.fromEntries(data);
      if (rental) {
        payload.additional_needs = data.getAll("additional_needs").join(", ");
        if (payload.end_time <= payload.start_time) {
          status.textContent =
            "Please choose an end time after the start time.";
          status.dataset.error = "true";
          status.focus();
          return;
        }
      }
      button.disabled = true;
      status.dataset.error = "false";
      status.textContent = "Sending your enquiry…";
      try {
        const response = await fetch(form.action, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(25000),
        });
        const result = await response.json();
        if (!response.ok)
          throw new Error(
            result.error ||
              "Your enquiry could not be saved. Please try again.",
          );
        status.textContent =
          result.message || "Your enquiry has been received.";
        form.reset();
      } catch (error) {
        status.dataset.error = "true";
        status.textContent =
          error.name === "TimeoutError"
            ? "We could not confirm receipt. Please contact the church before submitting again."
            : error.message ||
              "Connection interrupted. Please contact the church to confirm receipt.";
      } finally {
        button.disabled = false;
        status.focus({ preventScroll: true });
      }
    });
  });

const slides = [...document.querySelectorAll(".mySlides")];
const dots = [...document.querySelectorAll("[data-gallery-index]")];
const venueGallery = document.querySelector(".slideshow-container");
const galleryPlayback = document.querySelector("[data-gallery-playback]");
const galleryDelay = 1500;
let slideIndex = 0;
let galleryPaused = reducedMotion.matches;
let galleryHovered = false;
let galleryTimer;
let galleryReady = false;

function clearGalleryTimer() {
  window.clearTimeout(galleryTimer);
}

function canAutoAdvanceGallery() {
  return (
    galleryReady &&
    !galleryPaused &&
    !galleryHovered &&
    !document.hidden &&
    venueGallery?.closest(".page")?.classList.contains("active") &&
    !venueGallery.contains(document.activeElement)
  );
}

function scheduleNextGallerySlide() {
  clearGalleryTimer();
  if (!canAutoAdvanceGallery()) return;
  galleryTimer = window.setTimeout(() => {
    if (canAutoAdvanceGallery()) showSlide(slideIndex + 1);
    scheduleNextGallerySlide();
  }, galleryDelay);
}

function showSlide(index) {
  if (!slides.length) return;
  slideIndex = (index + slides.length) % slides.length;
  slides.forEach((slide, i) => {
    slide.style.display = i === slideIndex ? "block" : "none";
  });
  dots.forEach((dot, i) =>
    dot.setAttribute("aria-current", String(i === slideIndex)),
  );
  scheduleNextGallerySlide();
}
slides.forEach((slide, i) => {
  const image = slide.querySelector("img");
  image.alt = `Church venue photograph ${i + 1} of ${slides.length}`;
  image.loading = "lazy";
  image.addEventListener("error", () =>
    image.replaceWith(
      node(
        "p",
        "This venue photograph is currently unavailable.",
        "event-state",
      ),
    ),
  );
});
document.querySelectorAll("[data-gallery-step]").forEach((button) => {
  button.addEventListener("click", () =>
    showSlide(slideIndex + Number(button.dataset.galleryStep)),
  );
});
dots.forEach((button, i) =>
  button.addEventListener("click", () => showSlide(i)),
);
showSlide(0);

function updateGalleryPlayback() {
  if (!galleryPlayback) return;
  galleryPlayback.textContent = galleryPaused ? "Play slideshow" : "Pause slideshow";
  galleryPlayback.setAttribute("aria-pressed", String(galleryPaused));
}

if (venueGallery && slides.length > 1) {
  venueGallery.addEventListener("mouseenter", () => {
    galleryHovered = true;
    clearGalleryTimer();
  });
  venueGallery.addEventListener("mouseleave", () => {
    galleryHovered = false;
    scheduleNextGallerySlide();
  });
  venueGallery.addEventListener("focusin", clearGalleryTimer);
  venueGallery.addEventListener("focusout", () => {
    window.setTimeout(scheduleNextGallerySlide, 0);
  });
  galleryPlayback?.addEventListener("click", () => {
    galleryPaused = !galleryPaused;
    updateGalleryPlayback();
    scheduleNextGallerySlide();
  });
  reducedMotion.addEventListener("change", () => {
    galleryPaused = reducedMotion.matches;
    updateGalleryPlayback();
    scheduleNextGallerySlide();
  });
  document.addEventListener("visibilitychange", () => {
    scheduleNextGallerySlide();
  });
  window.addEventListener("dcc:route-change", scheduleNextGallerySlide);
  galleryReady = true;
  updateGalleryPlayback();
  scheduleNextGallerySlide();
}
