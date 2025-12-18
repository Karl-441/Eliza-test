# Client Architecture Refactoring: Art Style Synchronization

## 1. Overview
This document outlines the architectural changes to align the Eliza Client's visual style with the Server's "Tactical" aesthetic (Griffin & Kryuger / Sangvis Ferri style). The goal is to establish a server-driven rendering pipeline where art assets and style parameters are dynamically synchronized.

## 2. Architecture Design

### 2.1 Server-Side Theme Provider
- **Module**: `server.routers.theme`
- **Responsibility**: Serves the authoritative source of truth for visual style.
- **Data Model**:
  - `ThemeConfig`: Root configuration object.
  - `ThemeColors`: Semantic color definitions (Primary, Secondary, Accent, Danger, etc.).
  - `Assets`: URLs for logos, background particles, and icons.
- **Endpoints**:
  - `GET /api/v1/theme/config`: Returns full JSON configuration.
  - `GET /api/v1/theme/checksum`: Returns SHA256 hash of current config for cache validation.

### 2.2 Client-Side Theme Manager
- **Module**: `client.core.theme_manager`
- **Responsibility**: Fetches, caches, and applies theme settings.
- **Workflow**:
  1.  **Startup**: Client initializes `ThemeManager`.
  2.  **Handshake**: `ThemeManager` calls `/theme/checksum` to compare with local cache.
  3.  **Sync**: If mismatch, calls `/theme/config` to download new settings.
  4.  **Application**: Updates `client.ui.styles.GFTheme` static properties.
  5.  **Signal**: Emits `theme_updated` signal.
  6.  **Redraw**: `MainWindow` receives signal and calls `apply_styles()` and `update()` on widgets.

### 2.3 Rendering Pipeline
- **GFTheme Class**: Acts as a Singleton/Static Registry for style constants.
- **Dynamic QSS**: Qt Style Sheets are generated at runtime using `GFTheme` values, rather than hardcoded strings.
- **Components**: `TacticalButton`, `TacticalFrame` listen for style updates to refresh their internal drawing parameters (e.g., border colors, glow effects).

## 3. Technical Implementation

### 3.1 Resource Loading
- Assets (images) are currently referenced by URL paths in the config.
- Future improvement: `ThemeManager` should download and cache these images locally to `client/assets/cache/` to ensure offline capability.

### 3.2 Consistency Mechanism
- **Checksum Validation**: Implemented SHA256 hashing of the server config.
- **Polling**: Client checks for updates every 60 seconds (configurable).

## 4. Performance Considerations
- **Network**: Checksum endpoint is lightweight to minimize bandwidth.
- **Rendering**: Qt's `setStyleSheet` triggers a re-layout. Frequent updates should be avoided. The 60s polling interval balances freshness with performance.
- **Memory**: Theme config is small (< 10KB JSON), negligible impact.

## 5. Future Roadmap
- **Asset Caching**: Implement local file caching for large assets (background videos/images).
- **Style Versioning**: Support rolling back to previous visual versions.
- **User Customization**: Allow client overrides that persist locally but inherit server defaults.
