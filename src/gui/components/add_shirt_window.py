"""Window component for adding new shirts."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from typing import Dict, Callable
from PIL import Image, ImageTk

from src.models import STATUSES
from src.inventory_manager import add_shirt as mgr_add_shirt, update_shirt as mgr_update_shirt
from src.storage import save_shirts
from src.image_utils import save_image_from_path


class AddShirtWindow(tk.Toplevel):
    """Window for adding a new shirt."""
    
    def __init__(self, parent, shirts: list, refresh_callback: Callable, 
                 colors: Dict[str, str], fonts: Dict[str, tuple]) -> None:
        """Initialize add shirt window.
        
        Args:
            parent: Parent Tk window
            shirts: List of shirt objects
            refresh_callback: Callback to refresh main window
            colors: Color scheme dictionary
            fonts: Font dictionary
        """
        super().__init__(parent)
        self.shirts = shirts
        self.refresh_callback = refresh_callback
        self.colors = colors
        self.fonts = fonts
        self.pending_image_path = None
        self.current_image_photo = None
        
        self.title("Add New Shirt")
        self.configure(bg="#F5F5F5")
        
        # Set minimum and maximum sizes
        self.minsize(400, 300)
        self.maxsize(1000, 700)
        
        # Calculate responsive size (55% of parent or default 700x500)
        # Update parent window to get accurate dimensions
        try:
            parent.update_idletasks()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            # Only use parent dimensions if they're valid (not default 1x1)
            if parent_width > 100 and parent_height > 100:
                popup_width = max(400, min(1000, int(parent_width * 0.55)))
                popup_height = max(300, min(700, int(parent_height * 0.67)))
            else:
                # Fallback to default size for modal with image
                popup_width = 700
                popup_height = 500
        except:
            # Fallback to default size for modal with image
            popup_width = 700
            popup_height = 500
        
        self.geometry(f"{popup_width}x{popup_height}")
        
        self._build_widgets()
        
        # Center window properly
        self.update_idletasks()
        x = (self.winfo_screenwidth() - popup_width) // 2
        y = (self.winfo_screenheight() - popup_height) // 2
        self.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_widgets(self) -> None:
        """Build window widgets."""
        # Header
        header = tk.Frame(self, bg=self.colors['bg_panel'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="➕ Add New Shirt", font=self.fonts['title'],
                bg=self.colors['bg_panel'], fg=self.colors['text']).pack(padx=20, pady=12)
        
        # Main content area
        content = tk.Frame(self, bg=self.colors['bg_panel'], padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Top section: Image placeholder on left, Form fields on right
        top_section = tk.Frame(content, bg=self.colors['bg_panel'])
        top_section.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Left side: Image placeholder
        image_container = tk.Frame(top_section, bg=self.colors['bg_entry'], 
                                  relief=tk.FLAT, bd=1, highlightbackground=self.colors['border'],
                                  highlightthickness=1)
        image_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 15))
        image_container.configure(width=250, height=250)
        image_container.pack_propagate(False)
        
        self.image_label = tk.Label(image_container, text="📷\nNo Image\n\nClick here to add image", 
                                    anchor=tk.CENTER, justify=tk.CENTER,
                                    bg=self.colors['bg_entry'], fg=self.colors['text_light'],
                                    font=self.fonts['normal'], relief=tk.FLAT, bd=1, cursor='hand2')
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Make image placeholder clickable to add image
        self.image_label.bind("<Button-1>", lambda e: self._on_image_click())
        
        # Right side: Form fields (Name, Color, Size)
        right_fields = tk.Frame(top_section, bg=self.colors['bg_panel'])
        right_fields.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_fields, text="Name", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_name = ttk.Entry(right_fields, font=self.fonts['normal'])
        self.entry_name.pack(fill=tk.X, pady=(0, 12))
        self.entry_name.focus()
        
        tk.Label(right_fields, text="Color", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_color = ttk.Entry(right_fields, font=self.fonts['normal'])
        self.entry_color.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(right_fields, text="Size", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_size = ttk.Entry(right_fields, font=self.fonts['normal'])
        self.entry_size.pack(fill=tk.X, pady=(0, 12))
        
        # Middle section: Status dropdown (full width)
        tk.Label(content, text="Status", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.combo_status = ttk.Combobox(content, values=STATUSES, state="readonly", 
                                       font=self.fonts['normal'])
        self.combo_status.set(STATUSES[0])
        self.combo_status.pack(fill=tk.X, pady=(0, 15))
        
        # Bottom section: All buttons in one row
        btn_frame = tk.Frame(content, bg=self.colors['bg_panel'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        btn_add = ttk.Button(btn_frame, text="➕ Add Shirt", command=self._on_add,
                            style='Success.TButton', width=18)
        btn_add.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self._on_close,
                               style='TButton', width=18)
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.bind("<Return>", lambda e: self._on_add())
        self.bind("<Escape>", lambda e: self._on_close())
    
    def _on_image_click(self) -> None:
        """Handle image click - ask if user wants to add a photo."""
        resp = messagebox.askyesno("Add Image", "Do you want to add a photo?")
        if resp:
            self._on_add_image()
    
    def _on_add_image(self) -> None:
        """Handle image upload."""
        file_path = filedialog.askopenfilename(
            title="Select Shirt Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            self.pending_image_path = file_path
            self._update_image_preview(file_path)
    
    def _update_image_preview(self, image_path: str) -> None:
        """Update the image preview in the placeholder."""
        self.current_image_photo = None
        
        if not image_path or not os.path.exists(image_path):
            self.image_label.configure(image="", text="📷\nNo Image\n\nClick here to add image", 
                                      font=self.fonts['normal'], fg=self.colors['text_light'])
            return
        
        try:
            img = Image.open(image_path)
            img.thumbnail((230, 230), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.current_image_photo = photo
            self.image_label.configure(image=photo, text="", bg=self.colors['bg_entry'], cursor='hand2')
            # Re-bind click handler for when image is displayed (to allow replacement)
            self.image_label.bind("<Button-1>", lambda e: self._on_image_click())
        except Exception as e:
            self.image_label.configure(image="", text=f"Error loading image:\n{str(e)}",
                                      font=self.fonts['small'], fg=self.colors['danger'])
    
    def _on_add(self) -> None:
        """Handle adding shirt."""
        name = self.entry_name.get().strip()
        color = self.entry_color.get().strip()
        size = self.entry_size.get().strip()
        status = self.combo_status.get().strip()
        
        if not name or not color or not size:
            messagebox.showwarning("Missing Data", "Name, Color, and Size are required.")
            return
        if status not in STATUSES:
            messagebox.showwarning("Invalid Status", "Please select a valid status.")
            return
        
        try:
            shirt = mgr_add_shirt(self.shirts, name, color, size, status)
            
            if self.pending_image_path:
                try:
                    image_path = save_image_from_path(self.pending_image_path, shirt.id, 
                                                      os.path.basename(self.pending_image_path))
                    mgr_update_shirt(self.shirts, shirt.id, image_path=image_path)
                except Exception as e:
                    messagebox.showwarning("Image Upload", f"Shirt added but image upload failed: {str(e)}")
            
            save_shirts(self.shirts)
            self.refresh_callback()
            messagebox.showinfo("Success", f"Shirt #{shirt.id} added successfully!")
            self._on_close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _on_close(self) -> None:
        """Close window."""
        if hasattr(self.master, 'add_window'):
            self.master.add_window = None
        self.destroy()

