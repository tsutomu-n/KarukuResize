# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<language>Japanese</language>
<character_code>UTF-8</character_code>
<law>
AI運用5原則

第1原則： AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告し、y/nでユーザー確認を取り、yが返るまで一切の実行を停止する。

第2原則： AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。

第3原則： AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。

第4原則： AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。

第5原則： AIは全てのチャットの冒頭にこの5原則を逐語的に必ずや画面出力してから対応する。
</law>

<every_chat>
[AI運用5原則]

[main_output]

#[n] times. # n = increment each chat, end line, etc(#1, #2...)
</every_chat>

## Project Overview

KarukuResize is a Japanese-optimized image resizing and compression tool with both GUI and CLI interfaces. The name "Karuku" (軽く) means "light" in Japanese, emphasizing the tool's focus on reducing file sizes.

## Development Commands

### Build and Install
```bash
# Install in development mode using uv
uv pip install -e .

# Or using pip
pip install -e .
```

### Running the Application
```bash
# CLI mode
python -m resize_images --help
# or after installation
karukuresize-cli --help

# GUI mode
python -m resize_images_gui
# or after installation
karukuresize-gui
```

### Code Quality and Testing
```bash
# Run linting with ruff
ruff check .
ruff check . --fix  # Auto-fix issues

# Format code with ruff
ruff format .

# Run tests (when available)
pytest

# Run pre-commit hooks manually
pre-commit run --all-files
```

## Architecture

### Core Modules
- **resize_core.py**: Core image processing logic, file handling utilities, and error handling. All image manipulation, path normalization, and safety checks are implemented here.
- **resize_images.py**: CLI implementation using argparse. Handles command-line arguments, progress display with tqdm, and batch processing orchestration.
- **resize_images_gui.py**: GUI implementation using CustomTkinter. Provides both single-file and batch processing modes with a modern interface.

### Key Design Patterns
1. **Japanese Environment Support**: All modules include comprehensive Japanese language support:
   - Error messages in Japanese via `get_japanese_error_message()`
   - Unicode path handling with proper normalization
   - Windows long path support (>260 characters)
   - Emoji and special character handling in filenames

2. **Error Handling**: Centralized error handling with:
   - Automatic retry mechanisms
   - Detailed logging with loguru
   - Graceful degradation for non-critical errors
   - User-friendly Japanese error messages

3. **Progress Tracking**: Both CLI and GUI implement progress tracking:
   - CLI uses tqdm for console progress bars
   - GUI uses CustomTkinter progress bars with threading
   - Resume capability for interrupted batch operations

### Important Implementation Details
- The project uses flat module structure (no package directory) with direct imports
- Entry points are defined in pyproject.toml pointing to main functions
- All path operations use `pathlib.Path` with proper Windows long path handling
- Image processing preserves EXIF data by default but can be configured
- Disk space is checked before operations to prevent failures

### Recent Updates
- GUI batch processing functionality has been implemented (previously TODO)
  - `start_batch_process()` handles validation and thread management
  - `process_batch_worker()` performs actual batch processing with progress tracking
  - `cancel_batch_process()` allows graceful interruption
- The GUI now has full feature parity with the CLI for batch operations