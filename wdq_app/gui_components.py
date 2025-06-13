"""GUI component builders for WDQ Analyzer."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Tuple, Optional


class GUIComponents:
    """Factory class for creating GUI components."""
    
    @staticmethod
    def create_labeled_frame(parent: ttk.Frame, title: str, padding: int = 10) -> ttk.LabelFrame:
        """Create a labeled frame."""
        frame = ttk.LabelFrame(parent, text=title, padding=padding)
        return frame
    
    @staticmethod
    def create_entry_with_label(parent: ttk.Frame, label_text: str, 
                               variable: tk.StringVar, width: int = 10) -> Tuple[ttk.Label, ttk.Entry]:
        """Create a label-entry pair."""
        label = ttk.Label(parent, text=label_text)
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        return label, entry
    
    @staticmethod
    def create_button_row(parent: ttk.Frame, buttons: List[Tuple[str, Callable]], 
                         pack_side: str = tk.LEFT, padx: int = 5):
        """Create a row of buttons."""
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(parent, text=text, command=command)
            btn.pack(side=pack_side, padx=(0 if i == 0 else padx, 0))
    
    @staticmethod
    def create_treeview_with_scrollbar(parent: ttk.Frame, columns: List[str], 
                                     height: int = 10) -> Tuple[ttk.Treeview, ttk.Scrollbar]:
        """Create a treeview with scrollbar."""
        # Container frame
        tree_frame = ttk.Frame(parent)
        
        # Treeview
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=height)
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return tree, scrollbar, tree_frame
    
    @staticmethod
    def create_status_label(parent: ttk.Frame, text: str = "", 
                          foreground: str = "blue") -> ttk.Label:
        """Create a status label."""
        label = ttk.Label(parent, text=text, foreground=foreground)
        return label