"use strict";

document
  .querySelector("[data-show-password]")
  ?.addEventListener("click", (event) => {
    const input = document.querySelector("#password");
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    event.currentTarget.textContent = show ? "Hide password" : "Show password";
    event.currentTarget.setAttribute("aria-pressed", String(show));
  });

const menuToggle = document.querySelector(".menu-toggle");
const adminSidebar = document.querySelector("#admin-sidebar");
function closeAdminMenu(focus = false) {
  if (!adminSidebar || !menuToggle) return;
  adminSidebar.classList.remove("is-open");
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.textContent = "Menu";
  if (focus) menuToggle.focus();
}
menuToggle?.addEventListener("click", () => {
  const open = menuToggle.getAttribute("aria-expanded") !== "true";
  adminSidebar.classList.toggle("is-open", open);
  menuToggle.setAttribute("aria-expanded", String(open));
  menuToggle.textContent = open ? "Close" : "Menu";
});
document.addEventListener("keydown", (event) => {
  if (
    event.key === "Escape" &&
    menuToggle?.getAttribute("aria-expanded") === "true"
  )
    closeAdminMenu(true);
});
document.addEventListener("click", (event) => {
  if (
    !adminSidebar?.contains(event.target) &&
    !menuToggle?.contains(event.target)
  )
    closeAdminMenu();
});
document.addEventListener("focusin", (event) => {
  if (
    menuToggle?.getAttribute("aria-expanded") === "true" &&
    !adminSidebar.contains(event.target) &&
    !menuToggle.contains(event.target)
  ) {
    closeAdminMenu();
  }
});
matchMedia("(max-width: 800px)").addEventListener("change", () =>
  closeAdminMenu(),
);

document.querySelectorAll("[data-image-fallback]").forEach((image) => {
  function fallback() {
    const text = document.createElement("span");
    text.textContent = "Image unavailable";
    image.replaceWith(text);
  }
  image.addEventListener("error", fallback, { once: true });
  if (image.complete && !image.naturalWidth) fallback();
});

function openLinkedRecord() {
  if (!location.hash) return;
  const record = document.getElementById(
    decodeURIComponent(location.hash.slice(1)),
  );
  if (record instanceof HTMLDetailsElement) {
    record.open = true;
    record.querySelector("summary")?.focus({ preventScroll: true });
    record.scrollIntoView({ block: "start" });
  }
}

document.querySelectorAll("[data-list]").forEach((list) => {
  const records = [...list.querySelectorAll("[data-record]")];
  const search = list.querySelector("[data-search]");
  const dateFilter = list.querySelector("[data-date-filter]");
  const spaceFilter = list.querySelector("[data-space-filter]");
  const pagination = list.querySelector("[data-pagination]");
  let page = 1;
  const pageSize = 10;
  function render(reset = false) {
    if (reset) page = 1;
    const query = search.value.trim().toLocaleLowerCase();
    // Date-only comparisons in Sri Lankan time avoid treating today's requests as past.
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Colombo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(new Date());
    const get = (type) => parts.find((part) => part.type === type).value;
    const today = `${get("year")}-${get("month")}-${get("day")}`;
    const thisMonth = today.slice(0, 7);
    const year = Number(get("year")),
      month = Number(get("month"));
    const nextMonth = `${month === 12 ? year + 1 : year}-${String(month === 12 ? 1 : month + 1).padStart(2, "0")}`;
    const matches = records.filter((record) => {
      const textMatches = (record.dataset.searchText || record.textContent)
        .toLocaleLowerCase()
        .includes(query);
      const date = (record.dataset.date || "").slice(0, 10);
      const filter = dateFilter?.value || "";
      const dateMatches =
        !filter ||
        (filter === "upcoming" && date >= today) ||
        (filter === "past" && date && date < today) ||
        (filter === "this-month" && date.startsWith(thisMonth)) ||
        (filter === "next-month" && date.startsWith(nextMonth));
      return (
        textMatches &&
        dateMatches &&
        (!spaceFilter?.value || record.dataset.space === spaceFilter.value)
      );
    });
    const maxPage = Math.max(1, Math.ceil(matches.length / pageSize));
    page = Math.min(page, maxPage);
    const visible = new Set(
      matches.slice((page - 1) * pageSize, page * pageSize),
    );
    records.forEach((record) => {
      record.hidden = !visible.has(record);
    });
    list.querySelector("[data-result-count]").textContent =
      `${matches.length} of ${records.length} records`;
    list.querySelector("[data-no-results]").hidden = matches.length > 0;
    pagination.hidden = maxPage <= 1;
    list.querySelector("[data-page-status]").textContent =
      `Page ${page} of ${maxPage}`;
    list.querySelector("[data-page-prev]").disabled = page === 1;
    list.querySelector("[data-page-next]").disabled = page === maxPage;
  }
  search.addEventListener("input", () => render(true));
  dateFilter?.addEventListener("change", () => render(true));
  spaceFilter?.addEventListener("change", () => render(true));
  list.querySelector("[data-reset-filters]")?.addEventListener("click", () => {
    search.value = "";
    if (dateFilter) dateFilter.value = "";
    if (spaceFilter) spaceFilter.value = "";
    render(true);
  });
  list.querySelector("[data-page-prev]").addEventListener("click", () => {
    page--;
    render();
  });
  list.querySelector("[data-page-next]").addEventListener("click", () => {
    page++;
    render();
  });
  if (location.hash) {
    const linked = records.find((record) => `#${record.id}` === location.hash);
    if (linked) page = Math.floor(records.indexOf(linked) / pageSize) + 1;
  }
  render();
});
openLinkedRecord();
window.addEventListener("hashchange", openLinkedRecord);

const deleteDialog = document.querySelector("#delete-dialog");
let deletingForm;
document.querySelectorAll("[data-delete-event]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    deletingForm = form;
    deleteDialog.querySelector("#delete-description").textContent =
      form.dataset.eventTitle;
    deleteDialog.returnValue = "";
    deleteDialog.showModal();
    deleteDialog.querySelector('[value="cancel"]').focus();
  });
});
deleteDialog?.addEventListener("close", () => {
  if (deleteDialog.returnValue === "confirm" && deletingForm) {
    deletingForm.querySelector("button").disabled = true;
    HTMLFormElement.prototype.submit.call(deletingForm);
  }
  deletingForm = null;
});

const editor = document.querySelector("[data-event-editor]");
if (editor) {
  let dirty = false,
    submitting = false,
    imageUrl;
  const title = editor.querySelector("#title");
  const date = editor.querySelector("#event_date");
  const description = editor.querySelector("#description");
  const image = editor.querySelector("#image");
  const previewImage = editor.querySelector("[data-preview-image]");
  const originalImage = previewImage.cloneNode(true);
  const error = editor.querySelector("[data-upload-error]");
  const clear = editor.querySelector("[data-clear-upload]");
  function updatePreview() {
    editor.querySelector("[data-preview-title]").textContent =
      title.value.trim() || "Your event title";
    editor.querySelector("[data-preview-description]").textContent =
      description.value || "Your event description will appear here.";
    editor.querySelector("[data-preview-date]").textContent = date.value
      ? new Date(`${date.value}T00:00:00`).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "long",
          year: "numeric",
        })
      : "Event date";
  }
  editor.addEventListener("input", () => {
    dirty = true;
    updatePreview();
  });
  function resetImage() {
    image.value = "";
    image.setCustomValidity("");
    error.textContent = "";
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    previewImage.replaceChildren(
      ...[...originalImage.childNodes].map((node) => node.cloneNode(true)),
    );
    clear.hidden = true;
  }
  clear.addEventListener("click", () => {
    resetImage();
    dirty = true;
  });
  image.addEventListener("change", () => {
    dirty = true;
    const file = image.files[0];
    if (!file) {
      resetImage();
      return;
    }
    clear.hidden = false;
    const validTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    if (!validTypes.includes(file.type) || file.size > 8 * 1024 * 1024) {
      const message =
        "Choose a JPG, PNG, GIF or WebP image no larger than 8 MB.";
      error.textContent = message;
      image.setCustomValidity(message);
      return;
    }
    error.textContent = "";
    image.setCustomValidity("");
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    imageUrl = URL.createObjectURL(file);
    const img = document.createElement("img");
    img.alt = "Selected event image preview";
    img.src = imageUrl;
    img.addEventListener("error", () => {
      error.textContent =
        "This image cannot be opened. Choose a different image.";
      image.setCustomValidity(error.textContent);
    });
    previewImage.replaceChildren(img);
  });
  editor.addEventListener("submit", (event) => {
    if (submitting) {
      event.preventDefault();
      return;
    }
    submitting = true;
    dirty = false;
    const button = editor.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = "Saving…";
    editor.querySelector("[data-editor-status]").textContent =
      "Saving your event. Please wait.";
  });
  window.addEventListener("beforeunload", (event) => {
    if (dirty && !submitting) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  window.addEventListener("pageshow", () => {
    submitting = false;
    const button = editor.querySelector('button[type="submit"]');
    button.disabled = false;
    button.textContent = location.pathname.includes("/edit/")
      ? "Save changes"
      : "Publish event";
    editor.querySelector("[data-editor-status]").textContent = "";
  });
}
