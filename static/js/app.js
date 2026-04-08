// Dark mode toggle
document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  const html = document.documentElement;
  const icon = toggle.querySelector("i");

  // Load saved preference
  const saved = localStorage.getItem("theme");
  if (saved) {
    html.setAttribute("data-bs-theme", saved);
    updateIcon(saved);
  } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    html.setAttribute("data-bs-theme", "dark");
    updateIcon("dark");
  }

  toggle.addEventListener("click", function () {
    const current = html.getAttribute("data-bs-theme");
    const next = current === "dark" ? "light" : "dark";
    html.setAttribute("data-bs-theme", next);
    localStorage.setItem("theme", next);
    updateIcon(next);
  });

  function updateIcon(theme) {
    if (theme === "dark") {
      icon.className = "bi bi-sun-fill";
    } else {
      icon.className = "bi bi-moon-fill";
    }
  }

  // Drag and drop reorder (basic)
  const todoList = document.getElementById("todo-list");
  if (todoList) {
    let draggedEl = null;

    todoList.querySelectorAll(".list-group-item").forEach(function (item) {
      item.setAttribute("draggable", "true");

      item.addEventListener("dragstart", function (e) {
        draggedEl = item;
        item.classList.add("opacity-50");
        e.dataTransfer.effectAllowed = "move";
      });

      item.addEventListener("dragend", function () {
        item.classList.remove("opacity-50");
        draggedEl = null;
      });

      item.addEventListener("dragover", function (e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
      });

      item.addEventListener("drop", function (e) {
        e.preventDefault();
        if (draggedEl && draggedEl !== item) {
          const rect = item.getBoundingClientRect();
          const midY = rect.top + rect.height / 2;
          if (e.clientY < midY) {
            todoList.insertBefore(draggedEl, item);
          } else {
            todoList.insertBefore(draggedEl, item.nextSibling);
          }
          saveOrder();
        }
      });
    });

    function saveOrder() {
      const items = [];
      todoList.querySelectorAll(".list-group-item").forEach(function (el) {
        const id = el.getAttribute("data-id");
        if (id) items.push(id);
      });

      const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      );
      const token = csrfToken
        ? csrfToken.value
        : document.cookie
            .split("; ")
            .find((row) => row.startsWith("csrftoken="))
            ?.split("=")[1];

      fetch("/reorder/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": token || "",
        },
        body: JSON.stringify({ items: items }),
      });
    }
  }
});
