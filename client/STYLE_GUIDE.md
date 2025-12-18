# Tactical UI Style Guide

## 1. Design Philosophy
Based on [GFWiki](https://www.gfwiki.org/w/%E9%A6%96%E9%A1%B5) and "Girls' Frontline" art direction.
- **Theme**: Military Tactical / Sci-Fi
- **Keywords**: Precision, Data-driven, Holographic, Dark Mode

## 2. Color Palette (色板)

| Usage | Color Code | Description |
|-------|------------|-------------|
| **Background** | `#0D1A2B` | Deep Blue/Black (Main Background) |
| **Accent** | `#F0C419` | Tactical Gold (Primary Action/Highlight) |
| **Accent Hover** | `#FFD700` | Brighter Gold (Hover State) |
| **Text Primary** | `#E0E0E0` | High Contrast Text |
| **Text Secondary** | `#A0A0A0` | Metadata / Subtitles |
| **Border** | `#F0C419` | Standard Component Border |
| **Grid Lines** | `rgba(255, 255, 255, 0.15)` | Background Grid (15-20% Opacity) |
| **Warning** | `#FF4444` | Alerts / Warnings |
| **Error** | `#FF0000` | Critical Failures |

## 3. Typography (字体规范)

**Font Family**: `Source Han Sans` (Preferred) > `Microsoft YaHei` (Fallback) > `Segoe UI`

| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| **H1** | 24px | Bold | Main Headers, Modal Titles |
| **H2** | 20px | Bold | Section Headers |
| **H3** | 18px | Bold | Card Titles |
| **Body** | 14px | Medium | Standard Text, Inputs |
| **Small** | 12px | Regular | Labels, Metadata, Timestamps |
| **Code** | 12px | Regular | Logs, Raw Data (Font: Consolas) |

## 4. Spacing System (间距系统)

Based on an **8px** grid system.

- **XS**: 4px (Minimal separation)
- **S**: 8px (Related items)
- **M**: 16px (Component padding)
- **L**: 24px (Section separation)
- **XL**: 32px (Layout margins)

## 5. Component Specifications

### Buttons (TacticalButton)
- **Height**: 48px (Minimum for touch targets)
- **Shape**: Rectangular with cut corners (10px cut)
- **Border**: 1px Solid Accent
- **Background**: Accent (20% Opacity) -> Hover (80% Opacity)
- **Interaction**: Glow effect on hover

### Dialogs
- **Background**: Main Background (#0D1A2B)
- **Border**: 2px Solid Accent
- **Overlay**: Semi-transparent black (50%)

### Visual Effects
- **Particles**: WebGL/OpenGL accelerated, 500-800 particles, floating animation.
- **Scanlines**: Radar charts and overlays include a rotating scan line.
- **Glow**: Critical elements have a pulse or static glow effect.

## 6. Layout & Responsiveness
- **Desktop**: 1920x1080
- **Notebook**: 1600x900
- **Tablet**: 1366x768 (Mobile layout triggers < 900px)
