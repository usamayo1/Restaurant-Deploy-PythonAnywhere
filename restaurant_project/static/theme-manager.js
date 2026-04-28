(function () {
    const STORAGE_KEY = "restaurant_theme";
    const DEFAULT_THEME = document.documentElement.getAttribute("data-theme") || "default";
    const THEMES = ["default", "light", "olive", "sunset"];

    function applyTheme(themeName) {
        const safeTheme = THEMES.includes(themeName) ? themeName : DEFAULT_THEME;
        document.documentElement.setAttribute("data-theme", safeTheme);
        return safeTheme;
    }

    function setTheme(themeName) {
        const appliedTheme = applyTheme(themeName);
        try {
            localStorage.setItem(STORAGE_KEY, appliedTheme);
        } catch (error) {
        }
        return appliedTheme;
    }

    function getTheme() {
        return document.documentElement.getAttribute("data-theme") || DEFAULT_THEME;
    }

    function initializeTheme() {
        let savedTheme = getTheme();
        try {
            savedTheme = localStorage.getItem(STORAGE_KEY) || savedTheme;
        } catch (error) {
            savedTheme = getTheme();
        }
        applyTheme(savedTheme);
    }

    initializeTheme();

    window.ThemeManager = {
        setTheme,
        getTheme,
        resetTheme: function () {
            try {
                localStorage.removeItem(STORAGE_KEY);
            } catch (error) {
            }
            return applyTheme(DEFAULT_THEME);
        },
        listThemes: function () {
            return [...THEMES];
        },
    };
})();
