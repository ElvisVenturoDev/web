(() => {
    const grid = document.querySelector("[data-catalog-grid]");
    const search = document.querySelector("#product-search");
    const category = document.querySelector("#category-filter");
    const sort = document.querySelector("#sort-products");
    const empty = document.querySelector("[data-catalog-empty]");
    const count = document.querySelector("[data-catalog-count]");
    const reset = document.querySelector("[data-catalog-reset]");
    const tabs = [...document.querySelectorAll("[data-category-tabs] [data-category]")];

    if (!grid || !search || !category || !sort || !empty) {
        return;
    }

    const cards = [...grid.querySelectorAll("[data-catalog-card]")];
    const originalOrder = new Map(cards.map((card, index) => [card, index]));
    const favoritesKey = "santaclara-favorites";

    const readFavorites = () => {
        try {
            const stored = JSON.parse(localStorage.getItem(favoritesKey) || "[]");
            return new Set(Array.isArray(stored) ? stored : []);
        } catch (error) {
            console.warn("No se pudieron leer los favoritos guardados.", error);
            return new Set();
        }
    };

    const favorites = readFavorites();

    const saveFavorites = () => {
        try {
            localStorage.setItem(favoritesKey, JSON.stringify([...favorites]));
        } catch (error) {
            // El catálogo sigue funcionando aunque no pueda persistir los favoritos.
            console.warn("No se pudieron guardar los favoritos.", error);
        }
    };

    const isFeatured = (card) => card.dataset.featured === "true";

    const syncTabs = () => {
        tabs.forEach((tab) => {
            const active = tab.dataset.category === category.value;
            window.applyCategoryTabState(tab, active);
        });
    };

    const matchesCategory = (card, selectedCategory) => {
        if (selectedCategory === "all") {
            return true;
        }
        if (selectedCategory === "featured") {
            return isFeatured(card);
        }
        return card.dataset.category === selectedCategory;
    };

    const filterCards = (query, selectedCategory) =>
        cards.filter((card) => {
            const name = card.dataset.name.toLocaleLowerCase("es");
            return name.includes(query) && matchesCategory(card, selectedCategory);
        });

    const syncCardVisibility = (matches) => {
        cards.forEach((card) => {
            const isMatch = matches.includes(card);
            if (isMatch && card.hidden) {
                card.hidden = false;
                card.style.animation = "none";
                // Un elemento que vuelve a mostrarse no reinicia su animación sin forzar el reflow.
                void card.offsetHeight;
                card.style.animation = "card-enter 0.4s cubic-bezier(0.22, 1, 0.36, 1) both";
            } else if (!isMatch) {
                card.hidden = true;
            }
        });
    };

    const compareCards = (selectedSort) => (first, second) => {
        if (selectedSort === "name") {
            return first.dataset.name.localeCompare(second.dataset.name, "es");
        }
        if (selectedSort === "price") {
            return Number(first.dataset.price) - Number(second.dataset.price);
        }
        if (selectedSort === "price-desc") {
            return Number(second.dataset.price) - Number(first.dataset.price);
        }
        // "Destacados": primero los destacados, luego por calificación y orden original
        const featuredDiff = Number(isFeatured(second)) - Number(isFeatured(first));
        if (featuredDiff !== 0) {
            return featuredDiff;
        }
        const ratingDiff = Number(second.dataset.rating || 0) - Number(first.dataset.rating || 0);
        if (ratingDiff !== 0) {
            return ratingDiff;
        }
        return originalOrder.get(first) - originalOrder.get(second);
    };

    const updateCount = (total) => {
        if (!count) {
            return;
        }
        const label = total === 1 ? "habitación disponible" : "habitaciones disponibles";
        count.textContent = `${total} ${label}`;
    };

    const updateCatalog = () => {
        const query = search.value.trim().toLocaleLowerCase("es");
        const matches = filterCards(query, category.value);

        syncCardVisibility(matches);
        matches.sort(compareCards(sort.value));
        matches.forEach((card) => grid.append(card));

        empty.hidden = matches.length > 0;
        updateCount(matches.length);
    };

    const resetFilters = () => {
        search.value = "";
        category.value = "all";
        sort.value = "featured";
        syncTabs();
        updateCatalog();
        search.focus();
    };

    cards.forEach((card) => {
        const button = card.querySelector("[data-favorite]");
        const productId = card.dataset.productId;
        const productName = card.dataset.name;

        if (button) {
            const syncFavorite = () => {
                const selected = favorites.has(productId);
                button.setAttribute("aria-pressed", String(selected));
                button.setAttribute(
                    "aria-label",
                    `${selected ? "Quitar" : "Añadir"} ${productName} ${selected ? "de" : "a"} favoritos`,
                );
                const icon = button.querySelector("[data-favorite-icon]");
                if (icon) {
                    icon.textContent = selected ? "♥" : "♡";
                }
                button.classList.toggle("text-rose-500", selected);
            };

            button.addEventListener("click", () => {
                if (favorites.has(productId)) {
                    favorites.delete(productId);
                } else {
                    favorites.add(productId);
                }
                saveFavorites();
                syncFavorite();
                button.classList.remove("is-favorited");
                void button.offsetWidth;
                button.classList.add("is-favorited");
            });

            syncFavorite();
        }
    });

    search.addEventListener("input", updateCatalog);
    sort.addEventListener("change", updateCatalog);
    category.addEventListener("change", () => {
        syncTabs();
        updateCatalog();
    });

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            category.value = tab.dataset.category;
            syncTabs();
            updateCatalog();
        });
    });

    reset?.addEventListener("click", resetFilters);

    const focusSearch = new URLSearchParams(window.location.search).get("focus") === "search";
    if (focusSearch) {
        window.setTimeout(() => search.focus(), 0);
    }

    syncTabs();
    updateCatalog();
})();