/* =========================================================
   NOTIFICACIONES - SANTA CLARA
   Permite cerrar cualquier notificación marcada con
   [data-notification]: mensajes del servidor (flash), errores
   de formulario y avisos emergentes (toasts).
   ========================================================= */

(() => {
    const notificationSelector = "[data-notification]";
    const closeButtonClass = "notification-close";
    const closeLabels = { es: "Cerrar notificación", en: "Close notification" };

    const getCloseLabel = () => closeLabels[document.documentElement.lang] ?? closeLabels.es;

    const closeNotification = (notification) => {
        notification.remove();
    };

    const addCloseButton = (notification) => {
        if (notification.querySelector(`.${closeButtonClass}`)) return;

        const closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.className = closeButtonClass;
        closeButton.setAttribute("aria-label", getCloseLabel());
        closeButton.textContent = "×";
        closeButton.addEventListener("click", () => closeNotification(notification));

        notification.classList.add("notification-closable");
        notification.appendChild(closeButton);
    };

    const decorateAll = (root = document) => {
        root.querySelectorAll(notificationSelector).forEach(addCloseButton);
    };

    const watchNewNotifications = () => {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((element) => {
                    if (!(element instanceof HTMLElement)) return;
                    if (element.matches(notificationSelector)) addCloseButton(element);
                    decorateAll(element);
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    };

    // Escape cierra todas las notificaciones visibles.
    const closeAllOnEscape = (event) => {
        if (event.key !== "Escape") return;
        document.querySelectorAll(notificationSelector).forEach(closeNotification);
    };

    const init = () => {
        decorateAll();
        watchNewNotifications();
        document.addEventListener("keydown", closeAllOnEscape);
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
