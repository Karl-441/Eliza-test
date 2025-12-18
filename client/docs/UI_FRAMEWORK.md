
# UI Framework Documentation

## Overview
This UI framework is designed to replicate the "Girls' Frontline" tactical aesthetic while providing a modern, API-driven architecture.

## Architecture

### 1. Core Framework (`client/framework/`)
- **ThemeEngine (`theme.py`)**: Singleton `THEME` manages colors, fonts, and style constants. It supports dynamic updates via API.
- **Store (`state.py`)**: Singleton `STORE` manages application state using a Flux-like pattern with signals.
- **APIGateway (`api.py`)**: Centralized API client for fetching data and configurations.

### 2. Component Library (`client/components/`)
Follows Atomic Design principles:
- **Atoms (`atoms.py`)**: Basic building blocks (TacticalButton, TacticalMapMarker).
- **Molecules (`molecules.py`)**: Simple combinations (TacticalFrame, StatusIndicator).
- **Organisms (`organisms.py`)**: Complex UI sections (ParticleBackground, RadarChart).

## Usage Guide

### Using the Theme
```python
from client.framework.theme import THEME
from PyQt5.QtGui import QColor

# Get a color (returns hex string)
accent = THEME.get_color('ACCENT_COLOR')

# Use in QPainter
painter.setPen(QColor(accent))
```

### Creating a Component
Use the scaffold tool:
```bash
python client/tools/scaffold_ui.py MyNewButton --type atom
```

### State Management
```python
from client.framework.state import STORE

# Set state
STORE.set_state('user_level', 50)

# Listen to changes (via PyQt signals in your widget)
STORE.state_changed.connect(self.on_state_changed)
```

## Visual Style Guidelines
- **Colors**: Dark greys (#141414, #1F1F1F) with Gold/Yellow accents (#FFB400).
- **Shapes**: Cut corners (45-degree chamfer) on buttons and frames.
- **Typography**: Sans-serif (Segoe UI/Roboto) for body, Monospace (JetBrains Mono) for data.
- **Effects**: Drop shadows, inner glows, scanlines (overlay).

## Testing
Run the test suite:
```bash
python -m unittest discover client/tests
```
