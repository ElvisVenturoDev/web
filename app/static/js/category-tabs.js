/* Shared state for the catalog category tabs. */
window.applyCategoryTabState = (tab, active) => {
    tab.setAttribute("aria-pressed", String(active));
    tab.classList.toggle("bg-navy", active);
    tab.classList.toggle("text-white", active);
    tab.classList.toggle("border-transparent", active);
    tab.classList.toggle("border-slate-200", !active);
    tab.classList.toggle("bg-white", !active);
    tab.classList.toggle("text-slate-600", !active);
};
