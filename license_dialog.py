"""
License Activation Dialog
========================

Standalone license activation dialog that can be imported and used
by any application when license validation fails.

Author: License Management System
Date: July 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

# Import our license management library
try:
    from license_manager import LicenseManager
except ImportError:
    print("❌ Error: license_manager module not found!")
    sys.exit(1)


class LicenseActivationDialog:
    """
    License activation dialog with full functionality:
    - Display Hardware ID with copy function
    - Import license file option
    - Manual license token entry
    - Activation button
    """
    
    def __init__(self, parent=None, success_callback=None):
        self.license_manager = LicenseManager()
        self.result = False  # Will be True if license is successfully activated
        self.parent = parent
        self.success_callback = success_callback  # Callback to execute on successful activation
        self.dialog = None
        self.hw_id = self.license_manager.generate_hardware_id()
    
    def show_activation_dialog(self):
        """Show the license activation dialog and return activation result."""
        # Create dialog window
        self.dialog = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.dialog.title("License Activation Required")
        self.dialog.geometry("550x720")  # Increased height by 20 pixels (700 + 20)
        self.dialog.configure(bg='#f0f0f0')
        self.dialog.resizable(True, True)  # Make it resizable so user can adjust size
        self.dialog.minsize(500, 600)  # Set minimum size to ensure all content is visible
        
        # Make dialog modal
        if self.parent:
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
        
        # Setup UI
        self.setup_activation_ui()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Start dialog
        self.dialog.mainloop()
        
        return self.result
    
    def center_dialog(self):
        """Center the dialog on screen."""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_activation_ui(self):
        """Setup the activation dialog UI."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure main frame grid weights for proper expansion
        main_frame.grid_rowconfigure(0, weight=0)  # Title - fixed
        main_frame.grid_rowconfigure(1, weight=0)  # Message - fixed  
        main_frame.grid_rowconfigure(2, weight=0)  # Hardware info - fixed
        main_frame.grid_rowconfigure(3, weight=1)  # Activation methods - expandable
        main_frame.grid_rowconfigure(4, weight=0)  # Bottom buttons - fixed
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title with icon
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Error icon (using Unicode)
        icon_label = ttk.Label(
            title_frame, 
            text="🔒", 
            font=('Arial', 24),
            foreground='red'
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = ttk.Label(
            title_frame,
            text="License Activation Required",
            font=('Arial', 16, 'bold'),
            foreground='#d32f2f'
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Error message
        message_text = """This application requires a valid license to run.
Please activate your license using one of the methods below."""
        
        message_label = ttk.Label(
            main_frame,
            text=message_text,
            font=('Arial', 10),
            justify=tk.CENTER
        )
        message_label.pack(fill=tk.X, pady=(0, 20))
        
        # Hardware ID section
        hw_frame = ttk.LabelFrame(main_frame, text="Hardware Information", padding="15")
        hw_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(hw_frame, text="Hardware ID:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # Hardware ID display with copy button
        hw_display_frame = ttk.Frame(hw_frame)
        hw_display_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.hw_entry = ttk.Entry(
            hw_display_frame, 
            font=('Courier', 10), 
            state='readonly'
        )
        self.hw_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.hw_entry.config(state='normal')
        self.hw_entry.insert(0, self.hw_id)
        self.hw_entry.config(state='readonly')
        
        copy_btn = ttk.Button(
            hw_display_frame,
            text="📋 Copy",
            command=self.copy_hardware_id,
            width=10
        )
        copy_btn.pack(side=tk.RIGHT)
        
        hw_info_label = ttk.Label(
            hw_frame,
            text="Provide this Hardware ID to your software vendor to obtain a license.",
            font=('Arial', 9),
            foreground='#666666'
        )
        hw_info_label.pack(anchor=tk.W)
        
        # License activation methods
        activation_frame = ttk.LabelFrame(main_frame, text="License Activation", padding="15")
        activation_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Method 1: Import license file
        method1_frame = ttk.Frame(activation_frame)
        method1_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            method1_frame, 
            text="Method 1: Import License File", 
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W)
        
        file_frame = ttk.Frame(method1_frame)
        file_frame.pack(fill=tk.X, pady=(5, 0))
        
        import_btn = ttk.Button(
            file_frame,
            text="📁 Import License File",
            command=self.import_license_file,
            width=20
        )
        import_btn.pack(side=tk.LEFT)
        
        # Separator
        separator = ttk.Separator(activation_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(5, 15))
        
        # Method 2: Enter license token
        method2_frame = ttk.Frame(activation_frame)
        method2_frame.pack(fill=tk.X, pady=(0, 10))  # Don't expand, just fill X
        
        ttk.Label(
            method2_frame, 
            text="Method 2: Enter License Token", 
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W)
        
        token_info_label = ttk.Label(
            method2_frame,
            text="Paste your license token in the text area below:",
            font=('Arial', 9),
            foreground='#666666'
        )
        token_info_label.pack(anchor=tk.W, pady=(2, 5))
        
        # Token text area
        token_frame = ttk.Frame(method2_frame)
        token_frame.pack(fill=tk.X, pady=(0, 10))  # Don't expand the text area frame
        
        self.token_text = tk.Text(
            token_frame,
            height=5,  # Reduced height to ensure button is visible
            font=('Courier', 9),
            wrap=tk.WORD
        )
        self.token_text.pack(side=tk.LEFT, fill=tk.X, expand=True)  # Fill X but don't expand vertically
        
        token_scrollbar = ttk.Scrollbar(token_frame, orient=tk.VERTICAL, command=self.token_text.yview)
        token_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.token_text.config(yscrollcommand=token_scrollbar.set)
        
        # Token utility buttons
        token_btn_frame = ttk.Frame(method2_frame)
        token_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        paste_btn = ttk.Button(
            token_btn_frame,
            text="📋 Paste",
            command=self.paste_from_clipboard,
            width=12
        )
        paste_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(
            token_btn_frame,
            text="🗑️ Clear",
            command=self.clear_token,
            width=12
        )
        clear_btn.pack(side=tk.LEFT)
        
        # Activation button - prominently displayed and always visible
        activate_btn = ttk.Button(
            method2_frame,
            text="🔑 Activate",
            command=self.activate_license,
            width=20
        )
        activate_btn.pack(pady=(15, 0), fill=tk.X)  # Fill X and more padding
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Exit button
        exit_btn = ttk.Button(
            bottom_frame,
            text="❌ Exit Application",
            command=self.on_close
        )
        exit_btn.pack(side=tk.RIGHT)
        
        # Status label
        self.status_label = ttk.Label(
            bottom_frame,
            text="Please activate your license to continue.",
            font=('Arial', 9),
            foreground='#666666'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Set focus to token text area
        self.token_text.focus_set()
    
    def copy_hardware_id(self):
        """Copy hardware ID to clipboard."""
        try:
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(self.hw_id)
            self.dialog.update()
            
            self.status_label.config(
                text="Hardware ID copied to clipboard!",
                foreground='green'
            )
            
            # Show temporary tooltip
            self.show_tooltip("Hardware ID copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")
    
    def import_license_file(self):
        """Import license from file."""
        file_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select License File",
            filetypes=[
                ("License files", "*.dat *.lic *.key"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    license_token = f.read().strip()
                
                if self.validate_and_install_license(license_token):
                    self.result = True
                    
                    # Close dialog first
                    if self.dialog:
                        self.dialog.withdraw()
                    
                    # Execute success callback if provided
                    if self.success_callback:
                        self.success_callback()
                    
                    # Show success message
                    messagebox.showinfo(
                        "Success",
                        "License file imported and activated successfully!\n\n"
                        "Welcome to the application!"
                    )
                    
                    # Close dialog
                    if self.dialog:
                        self.dialog.quit()
                else:
                    messagebox.showerror(
                        "License Error",
                        "Failed to activate the license from the selected file.\n\n"
                        "Please verify that:\n"
                        "• The license file is valid\n"
                        "• The license is intended for this machine\n"
                        "• The license has not expired"
                    )
                    
            except Exception as e:
                messagebox.showerror(
                    "File Error",
                    f"Error reading license file:\n{str(e)}"
                )
    
    def paste_from_clipboard(self):
        """Paste license token from clipboard."""
        try:
            clipboard_content = self.dialog.clipboard_get()
            self.token_text.delete(1.0, tk.END)
            self.token_text.insert(1.0, clipboard_content)
            self.status_label.config(
                text="License token pasted from clipboard.",
                foreground='blue'
            )
        except tk.TclError:
            messagebox.showwarning(
                "Clipboard Empty",
                "The clipboard is empty or contains non-text data."
            )
    
    def clear_token(self):
        """Clear the token text area."""
        self.token_text.delete(1.0, tk.END)
        self.status_label.config(
            text="Token text area cleared.",
            foreground='#666666'
        )
    
    def activate_license(self):
        """Activate license from token text area."""
        license_token = self.token_text.get(1.0, tk.END).strip()
        
        if not license_token:
            messagebox.showwarning(
                "No Token",
                "Please enter a license token in the text area above."
            )
            self.token_text.focus_set()
            return
        
        self.status_label.config(
            text="Validating license token...",
            foreground='orange'
        )
        self.dialog.update()
        
        if self.validate_and_install_license(license_token):
            self.result = True
            
            # Close dialog first
            if self.dialog:
                self.dialog.withdraw()
            
            # Execute success callback if provided
            if self.success_callback:
                self.success_callback()
            
            # Show success message
            messagebox.showinfo(
                "Success",
                "License token activated successfully!\n\n"
                "Welcome to the application!"
            )
            
            # Close dialog
            if self.dialog:
                self.dialog.quit()
        else:
            self.status_label.config(
                text="License activation failed. Please check your token.",
                foreground='red'
            )
            messagebox.showerror(
                "Activation Failed",
                "Failed to activate the license token.\n\n"
                "Please verify that:\n"
                "• The license token is complete and correct\n"
                "• The license is intended for this machine\n"
                "• The license has not expired or been revoked"
            )
    
    def validate_and_install_license(self, license_token):
        """Validate and install the license token."""
        try:
            return self.license_manager.install_license(license_token)
        except Exception as e:
            print(f"License validation error: {e}")
            return False
    
    def show_tooltip(self, message):
        """Show a temporary tooltip message."""
        tooltip = tk.Toplevel(self.dialog)
        tooltip.wm_overrideredirect(True)
        tooltip.configure(bg='black')
        
        label = tk.Label(
            tooltip,
            text=message,
            bg='black',
            fg='white',
            font=('Arial', 9),
            padx=10,
            pady=5
        )
        label.pack()
        
        # Position tooltip
        x = self.dialog.winfo_x() + self.dialog.winfo_width() // 2
        y = self.dialog.winfo_y() + 100
        tooltip.geometry(f"+{x}+{y}")
        
        # Auto-hide after 2 seconds
        self.dialog.after(2000, tooltip.destroy)
    
    def on_close(self):
        """Handle dialog close event."""
        self.result = False
        if self.dialog:
            self.dialog.quit()


def show_license_activation_dialog(parent=None, success_callback=None):
    """
    Convenience function to show license activation dialog.
    Returns True if license was successfully activated, False otherwise.
    
    Args:
        parent: Parent window for the dialog
        success_callback: Function to call when license is successfully activated
    """
    dialog = LicenseActivationDialog(parent, success_callback)
    return dialog.show_activation_dialog()


if __name__ == "__main__":
    # Test the dialog standalone
    result = show_license_activation_dialog()
    print(f"License activation result: {result}")
