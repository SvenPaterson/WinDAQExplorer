# Test Data Directory

This directory is for sample WDQ files used in testing.

## Adding Sample Files

To enable full testing of the windaq.py module, place any sample .wdq files here:

- The tests will automatically use the first `.wdq` file found
- You can use any filename (e.g., `my_data.wdq`, `test_file.wdq`, etc.)
- Multiple files are fine - tests will use the first one found

## File Requirements

Sample files should:
- Be valid WDQ format files
- Contain multiple channels if possible
- Have meaningful channel names and units
- Be reasonably sized (< 10MB for CI/CD)

## Running Tests Without Sample Files

Tests will run without sample files, but will skip file-dependent tests. You'll see messages like:
```
SKIPPED [1] test_windaq.py:42: Sample file not found: wdq_app/tests/data/sample.wdq
```

## Creating Sample Files

You can create sample files by:
1. Using the WinDAQ application to record short data samples
2. Using the main application to load and re-save existing files
3. Asking the project maintainer for sample files

## .gitignore

Sample files should generally be excluded from git (they can be large binary files). Add them to .gitignore if needed.