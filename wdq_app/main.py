#!/usr/bin/env python3
"""
WDQ Data Analyzer - Main Entry Point

A tool for analyzing and visualizing WinDAQ (.wdq) data files.
"""

import sys

# Check for required dependencies
try:
    import tkinter as tk
    from tkinter import messagebox
    import numpy
    import pandas
    import matplotlib
    import windaq
except ImportError as e:
    # Try to show error in GUI if tkinter is available
    try:
        import tkinter as tk
        from tkinter import messagebox
        tk.Tk().withdraw()  # Hide the main window
        messagebox.showerror(
            "Missing Dependencies",
            f"Required package not found: {e.name}\n\n"
            "Please install required packages:\n"
            "pip install numpy pandas matplotlib python-windaq"
        )
    except:
        # Fallback to console error
        print(f"Error: Missing required package: {e.name}")
        print("Please install required packages:")
        print("pip install numpy pandas matplotlib python-windaq")
    
    sys.exit(1)

from wdq_analyzer import main

if __name__ == "__main__":
    main()