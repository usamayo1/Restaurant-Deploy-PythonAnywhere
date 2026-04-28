# Theme System Guide

This project now supports client-specific UI themes without changing backend/business logic.

## How it works

- Active theme is stored on `<html data-theme="...">`.
- Global default theme comes from **Admin → Site Settings → Brand Theme**.
- Optional browser override is persisted in `localStorage` under `restaurant_theme`.
- Theme files are loaded from `static/themes/` and override CSS variables only.
- Existing feature logic (cart, checkout, offers, tracking) remains untouched.

## Built-in themes

- `default`
- `light`
- `olive`
- `sunset`

## Admin Theme Picker (Global)

1. Open **Admin → Site Settings**.
2. In **Brand Theme**, choose:
   - `Default`
   - `Olive`
   - `Sunset`
3. Save.

This applies website-wide for all users.

## Runtime theme switching

Use browser console or your own admin/theme picker UI:

```js
ThemeManager.setTheme("olive");
ThemeManager.setTheme("sunset");
ThemeManager.setTheme("default");
```

Reset local browser override back to Admin-selected theme:

```js
ThemeManager.resetTheme();
```

Available themes:

```js
ThemeManager.listThemes();
```

## Add a new client theme

1. Create a new file in `static/themes/`, for example:
   - `static/themes/theme-client-hotel.css`
2. Add CSS variable overrides:

```css
[data-theme="client-hotel"] {
  --color-accent: #008a7a;
  --color-accent-strong: #00a896;
  --topbar-btn-active-bg-color: #008a7a;
  --checkout-btn-bg-color: #008a7a;
}
```

3. Add a `<link>` for that file in `templates/base.html`.
4. Add theme name in `static/theme-manager.js` `THEMES` array.
5. Switch theme:

```js
ThemeManager.setTheme("client-hotel");
```

## Section-specific customization (optional)

If a client requests style changes for only one section, use scoped selectors in the theme file:

```css
[data-theme="client-hotel"] .top-bar {
  --topbar-bg-color: #102422;
}

[data-theme="client-hotel"] .cart-page {
  --bill-box-bg-color: #1d2f2d;
}
```

This keeps global design consistent while allowing focused customizations.
