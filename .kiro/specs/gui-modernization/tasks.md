# Implementation Plan

## Task Overview

Convert the feature design into a series of coding tasks for GUI modernization with settings persistence and progress tracking.

## Implementation Tasks

- [ ] 1. Fix current file corruption and syntax errors
  - Remove duplicate method definitions
  - Fix indentation and syntax errors in gui_app.py
  - Ensure clean CustomTkinter imports only
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Implement SettingsManager class
  - Create SettingsManager class with JSON persistence
  - Define default settings schema
  - Implement load_settings() and save_settings() methods
  - Add error handling for file I/O operations
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 3. Integrate settings persistence into ResizeApp
  - Initialize SettingsManager in ResizeApp.__init__()
  - Implement _restore_settings() method
  - Implement _save_current_settings() method
  - Add _on_closing() handler for automatic settings save
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. Add directory memory functionality
  - Modify _select_files() to use and save last_input_dir
  - Modify _save_current() to use and save last_output_dir
  - Modify _batch_save() to use and save last_output_dir
  - _Requirements: 2.3_

- [ ] 5. Implement progress bar UI components
  - Add CTkProgressBar widget to main layout
  - Add cancel button for batch operations
  - Initially hide both components (pack_forget)
  - _Requirements: 3.1, 3.3_

- [ ] 6. Add progress tracking to batch save operation
  - Show progress bar and cancel button at start of _batch_save()
  - Update progress bar for each processed image
  - Update status label with current progress
  - Force UI updates with self.update()
  - _Requirements: 3.1, 3.2_

- [ ] 7. Implement batch operation cancellation
  - Add _cancel_batch_save() method
  - Set cancellation flag when cancel button clicked
  - Check cancellation flag in batch processing loop
  - Hide progress components when cancelled or completed
  - _Requirements: 3.3, 3.4, 3.5_

- [ ] 8. Enhance error handling and user feedback
  - Add try-catch blocks around all file operations
  - Provide clear error messages for common failure scenarios
  - Ensure application continues operation after individual errors
  - Add logging for debugging purposes
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 9. Apple-style design implementation
  - Define APPLE_COLORS palette with #6193c9 as core accent color
  - Change appearance mode from "dark" to "light"
  - Apply Apple-style colors to all buttons, frames, and UI elements
  - Update fonts to system fonts (Segoe UI on Windows, SF Pro on macOS)
  - Implement rounded corners and clean borders for Apple aesthetic
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 10. Integration testing and bug fixes
  - Test complete application workflow
  - Verify settings persistence across application restarts
  - Test batch processing with progress tracking and cancellation
  - Fix any discovered issues or edge cases
  - _Requirements: All requirements_