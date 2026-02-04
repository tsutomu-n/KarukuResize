# GUI Modernization Design

## Overview

This design outlines the complete modernization of KarukuResize GUI using CustomTkinter, implementing settings persistence and progress tracking for batch operations.

## Architecture

### Core Components

1. **ResizeApp (Main Application)**
   - Inherits from `customtkinter.CTk`
   - Manages overall application lifecycle
   - Coordinates between UI and business logic

2. **SettingsManager**
   - Handles settings persistence to JSON file
   - Provides default values and validation
   - Manages settings loading/saving lifecycle

3. **UI Components**
   - All widgets use CustomTkinter equivalents
   - Consistent dark theme styling
   - Responsive grid-based layout

## Components and Interfaces

### SettingsManager Class

```python
class SettingsManager:
    def __init__(self, settings_file: str = "karuku_settings.json")
    def load_settings(self) -> dict
    def save_settings(self, settings: dict)
```

**Settings Schema:**
```json
{
    "mode": "ratio|width|height|fixed",
    "ratio_value": "string",
    "width_value": "string", 
    "height_value": "string",
    "last_input_dir": "string",
    "last_output_dir": "string",
    "window_geometry": "string",
    "zoom_preference": "string"
}
```

### UI Layout Structure

```
ResizeApp (CTk)
├── Top Bar (CTkFrame)
│   ├── File Selection Button
│   ├── Help Button
│   ├── Mode Radio Buttons
│   ├── Input Fields (Dynamic)
│   ├── Action Buttons
│   └── Zoom ComboBox
├── Progress Bar (CTkProgressBar) [Hidden by default]
├── Cancel Button (CTkButton) [Hidden by default]
├── Main Content (Grid Layout)
│   ├── File List (CTkScrollableFrame)
│   └── Preview Pane (CTkFrame)
│       ├── Original Preview (CTkFrame + CTkCanvas)
│       └── Resized Preview (CTkFrame + CTkCanvas)
└── Status Bar (CTkLabel)
```

## Data Models

### ImageJob
```python
@dataclass
class ImageJob:
    path: Path
    image: Image.Image
    resized: Optional[Image.Image] = None
```

### Settings Dictionary
- Persistent storage for user preferences
- JSON serialization for cross-session persistence
- Default value fallbacks for missing keys

## Error Handling

### Validation Strategy
- Input validation using CustomTkinter's built-in validation
- Graceful error recovery with user-friendly messages
- Logging for debugging purposes

### File Operation Errors
- Try-catch blocks around all file I/O
- User notification for failed operations
- Continuation of batch operations despite individual failures

## Testing Strategy

### Manual Testing Checklist
1. **UI Consistency**
   - All elements use CustomTkinter styling
   - Dark theme applied consistently
   - No visual artifacts or layout issues

2. **Settings Persistence**
   - Settings saved on application close
   - Settings restored on application start
   - Default values used for missing settings

3. **Progress Tracking**
   - Progress bar updates during batch operations
   - Cancel functionality works correctly
   - UI remains responsive during processing

4. **Error Scenarios**
   - Invalid file formats handled gracefully
   - Network/disk errors don't crash application
   - Invalid input values provide clear feedback