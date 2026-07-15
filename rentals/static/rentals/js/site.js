(function () {
    function isoDate(date) {
        return date.toISOString().slice(0, 10);
    }

    function daysFromToday(days) {
        const date = new Date();
        date.setDate(date.getDate() + days);
        return date;
    }

    function setupActiveMenu() {
        const currentPath = window.location.pathname;
        document.querySelectorAll(".site-nav a, .manager-nav a").forEach((link) => {
            if (link.pathname === currentPath) {
                link.classList.add("is-active");
            }
        });
    }

    function setupDateShortcuts() {
        document.querySelectorAll("[data-date-form]").forEach((form) => {
            const startInput = form.querySelector('input[name="start_date"]');
            const endInput = form.querySelector('input[name="end_date"]');

            if (!startInput || !endInput || form.querySelector(".date-shortcuts")) {
                return;
            }

            const shortcuts = document.createElement("div");
            shortcuts.className = "date-shortcuts";
            shortcuts.innerHTML = [
                '<button type="button" data-start="1" data-days="1">Domani</button>',
                '<button type="button" data-start="3" data-days="2">Weekend</button>',
                '<button type="button" data-start="7" data-days="3">Settimana prossima</button>',
            ].join("");
            form.appendChild(shortcuts);

            shortcuts.addEventListener("click", (event) => {
                const button = event.target.closest("button");
                if (!button) {
                    return;
                }

                const startOffset = Number(button.dataset.start || 1);
                const days = Number(button.dataset.days || 1);
                startInput.value = isoDate(daysFromToday(startOffset));
                endInput.value = isoDate(daysFromToday(startOffset + days - 1));
                startInput.dispatchEvent(new Event("change", { bubbles: true }));
                endInput.dispatchEvent(new Event("change", { bubbles: true }));
            });
        });
    }

    function setupReservationSummary() {
        const reservationForm = document.querySelector("[data-reservation-form]");
        if (!reservationForm) {
            return;
        }

        const summary = reservationForm.querySelector("[data-booking-summary]");
        const rows = Array.from(reservationForm.querySelectorAll("[data-rental-row]"));

        function updateSummary() {
            let items = 0;
            let dailyTotal = 0;

            rows.forEach((row) => {
                const input = row.querySelector('input[name^="quantity_"]');
                const quantity = input ? Number(input.value || 0) : 0;
                const price = Number(String(row.dataset.price || "0").replace(",", "."));

                if (quantity > 0) {
                    items += quantity;
                    dailyTotal += quantity * price;
                }
            });

            if (!summary) {
                return;
            }

            if (items === 0) {
                summary.innerHTML = "<strong>Riepilogo rapido</strong><span>Seleziona le quantità per vedere il totale giornaliero stimato.</span>";
                return;
            }

            const formattedTotal = dailyTotal.toFixed(2).replace(".", ",");
            summary.innerHTML = `<strong>${items} articolo/i selezionati</strong><span>Totale stimato al giorno: ${formattedTotal} €</span>`;
        }

        rows.forEach((row) => {
            const input = row.querySelector('input[name^="quantity_"]');
            if (input) {
                input.addEventListener("input", updateSummary);
            }
        });
        updateSummary();
    }

    function setupManagerCategoryFilter() {
        const categoryFilter = document.querySelector("#category-filter");
        if (categoryFilter && categoryFilter.form) {
            categoryFilter.addEventListener("change", () => categoryFilter.form.submit());
        }
    }




    function setupTableSearch() {
        document.querySelectorAll("[data-table-search]").forEach((input) => {
            const tableId = input.dataset.tableSearch;
            const table = document.getElementById(tableId);
            if (!table) {
                return;
            }

            const rows = Array.from(table.querySelectorAll("tbody tr"));
            input.addEventListener("input", () => {
                const query = input.value.trim().toLowerCase();
                rows.forEach((row) => {
                    const text = row.innerText.toLowerCase();
                    row.classList.toggle("row-hidden", query !== "" && !text.includes(query));
                });
            });
        });
    }

    function setupFileInputPreview() {
        document.querySelectorAll('input[type="file"]').forEach((input) => {
            const note = input.closest("p") ? input.closest("p").querySelector("[data-file-preview]") : null;
            if (!note) {
                return;
            }

            input.addEventListener("change", () => {
                if (input.files && input.files.length > 0) {
                    note.textContent = "File selezionato: " + input.files[0].name;
                }
            });
        });
    }

    function setupConfirmForms() {
        document.querySelectorAll("form[data-confirm]").forEach((form) => {
            form.addEventListener("submit", (event) => {
                const message = form.dataset.confirm || "Confermi questa operazione?";
                if (!window.confirm(message)) {
                    event.preventDefault();
                }
            });
        });
    }

    function setupImageLightbox() {
        document.querySelectorAll(".product-image").forEach((image) => {
            image.addEventListener("click", (event) => {
                event.preventDefault();

                const overlay = document.createElement("div");
                overlay.className = "lightbox";
                overlay.innerHTML = `<button type="button" aria-label="Chiudi immagine">Chiudi</button><img src="${image.src}" alt="${image.alt || "Immagine prodotto"}">`;
                document.body.appendChild(overlay);

                overlay.addEventListener("click", (overlayEvent) => {
                    if (overlayEvent.target === overlay || overlayEvent.target.tagName === "BUTTON") {
                        overlay.remove();
                    }
                });
            });
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.documentElement.classList.add("js-ready");
        setupActiveMenu();
        setupDateShortcuts();
        setupReservationSummary();
        setupManagerCategoryFilter();
        setupTableSearch();
        setupFileInputPreview();
        setupConfirmForms();
        setupImageLightbox();
    });
}());
