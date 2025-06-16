# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WinDAQExplorer is a Python desktop application for analyzing and visualizing WinDAQ (.wdq) data acquisition files. The project has evolved from simple utilities to a modern GUI application with clean MVC architecture.

## Running the Application

**Primary entry point (recommended):**
```bash
python3 wdq_app/main.py
```

**Alternative entry points:**
- `python3 wdq_analyzer_app.py` - Legacy monolithic GUI
- `python3 main_torquestand.py` - Specialized torque analysis with batch processing
- `jupyter notebook main.ipynb` - Interactive data exploration

## Dependencies

Required packages are checked at runtime in `wdq_app/main.py`. Install with:
```bash
# Install system dependencies first (Ubuntu/Debian)
sudo apt-get install python3-tk

# Then install Python packages
pip install -r requirements.txt
```

## Architecture

**Modern Application Structure (wdq_app/):**
- `main.py` - Entry point with dependency validation
- `modern_wdq_analyzer.py` - Main application class and UI (WDQAnalyzer)
- `wdq_controller.py` - Business logic controller
- `data_processor.py` - Signal processing algorithms (static methods)
- `plot_manager.py` - Matplotlib integration and visualization
- `models.py` - Data models (ChannelConfig dataclass)
- `gui_components.py` - Reusable UI components
- `windaq.py` - Custom WinDAQ file format reader

**Key Design Patterns:**
- **MVC Architecture:** UI (modern_wdq_analyzer) → Controller (wdq_controller) → Data (models, data_processor)
- **Observer Pattern:** Controller updates UI through callbacks
- **Dataclass Models:** ChannelConfig for type-safe channel configuration

**Data Flow:**
1. WinDAQ files loaded via `windaq.py` module
2. Raw data stored in `original_data` dict, processed data in `processed_data`
3. Channel configurations manage display properties (axis assignment, labels, units)
4. PlotManager handles matplotlib integration with dual-axis support
5. DataProcessor provides static methods for signal processing operations

## Key Components

**WDQAnalyzer Class:** Main application window with paned layout (controls | plot area)
- Manages file loading, channel configuration, and plot updates
- Uses ttk styling for modern appearance
- Handles user interactions and data processing workflows

**DataProcessor Static Methods:**
- `apply_moving_average()` - Convolution-based smoothing
- `resample_data()` - Downsampling by integer factor
- `apply_low_pass_filter()` - FFT-based frequency filtering
- `remove_offset()`, `normalize_data()` - Signal conditioning

**PlotManager:** 
- Handles matplotlib figure embedded in tkinter
- Supports primary/secondary axis plotting
- Manages colors and legends automatically
- Export functionality for multiple formats

## File Handling

**WinDAQ File Structure:** Binary files with header containing channel metadata (annotations, units, sample rates). The custom `windaq.py` module handles parsing without external dependencies.

**Channel Configuration:** Each channel has name, units, and axis assignment (Primary/Secondary/Omit). Units are cleaned of null characters and control symbols.

## Development Notes

**Legacy Components:** 
- `wdq_analyzer_app.py` contains the old monolithic implementation
- Both versions share similar functionality but modern version has better separation of concerns

**Specialized Analysis:**
- `main_torquestand.py` includes torque-specific workflows and Excel report generation
- Contains speed vs. torque curve analysis and FFT processing

**Error Handling:** Modern application includes comprehensive validation and user-friendly error messages through tkinter messageboxes.

## Testing

**Test Structure:**
- `wdq_app/tests/` - All test files
- `pytest.ini` - Test configuration
- `run_tests.py` - Convenient test runner script

**Running Tests:**
```bash
# Run all tests
pytest wdq_app/tests/

# Run with coverage
pytest --cov=wdq_app --cov-report=html wdq_app/tests/

# Run specific test file
pytest wdq_app/tests/test_data_processor.py

# Using test runner script
python run_tests.py --coverage
python run_tests.py --unit
python run_tests.py --integration
```

**Test Categories:**
- **Unit Tests:** `test_data_processor.py`, `test_models.py` - Test individual functions and classes
- **Integration Tests:** `test_integration.py` - Test component interactions and data flow
- **File I/O Tests:** `test_windaq.py` - Test file reading (requires sample .wdq files in `wdq_app/tests/data/`)

**Adding Tests:** Follow pytest conventions. New test files should start with `test_` and contain test functions starting with `test_`. Use existing test files as templates for structure and patterns.