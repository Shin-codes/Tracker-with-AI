"""Card component for displaying shirt in e-commerce style."""
import tkinter as tk
import os
from typing import Dict, Callable, Optional
from PIL import Image, ImageTk

from src.models import Shirt
from src.image_utils import get_image_display_path


class ShirtCard(tk.Frame):
    """E-commerce style card for displaying a shirt."""
    
    def __init__(self, parent, shirt: Shirt, colors: Dict[str, str], 
                 fonts: Dict[str, tuple], on_click: Callable = None,
                 on_right_click: Callable = None, on_edit: Callable = None,
                 on_delete: Callable = None) -> None:
        """Initialize shirt card.
        
        Args:
            parent: Parent frame
            shirt: Shirt object to display
            colors: Color scheme dictionary
            fonts: Font dictionary
            on_click: Callback when card is clicked
            on_right_click: Callback when card is right-clicked
            on_edit: Callback when edit button is clicked
            on_delete: Callback when delete button is clicked
        """
        super().__init__(parent, bg=colors['bg_panel'], relief=tk.FLAT, bd=1)
        self.shirt = shirt
        self.colors = colors
        self.fonts = fonts
        self.on_click = on_click
        self.on_right_click = on_right_click
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.is_selected = False
        self.current_image_photo = None
        
        self.configure(highlightbackground=colors['border'], highlightthickness=1)
        
        # Initialize button widgets list before building card
        self._button_widgets = []
        
        self._build_card()
        
        # Bind click events only to the card itself, not recursively
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Button-3>", lambda e: self._on_right_click(e))
        
        # Bind click events to child widgets EXCEPT buttons and blue box
        self._bind_selective(self, "<Button-1>", lambda e: self._on_click())
        self._bind_selective(self, "<Button-3>", lambda e: self._on_right_click(e))
    
    def _bind_selective(self, widget, event, handler):
        """Selectively bind event to widget and children, skipping buttons and blue box."""
        try:
            # Skip binding if this is the blue box or any of its children
            if hasattr(self, '_blue_box_ref') and self._blue_box_ref:
                if widget == self._blue_box_ref:
                    return
                # Check if widget is a child of blue_box by traversing up parent chain
                temp_widget = widget
                while temp_widget:
                    if temp_widget == self._blue_box_ref:
                        return
                    temp_widget = temp_widget.master if hasattr(temp_widget, 'master') else None
                    if temp_widget == self:
                        break  # Reached card, stop checking
            
            # Skip buttons
            if isinstance(widget, tk.Button):
                return
            if widget in self._button_widgets:
                return
            
            # Bind to widget if it's not the card itself (card is already bound)
            if widget != self:
                widget.bind(event, handler)
            
            # Recursively bind to children
            for child in widget.winfo_children():
                self._bind_selective(child, event, handler)
        except:
            pass
    
    def _build_card(self) -> None:
        """Build the card UI."""
        # Set fixed size for card (no hover effect)
        self.configure(width=220, height=320)
        self.pack_propagate(False)
        
        # Card container with padding
        card_inner = tk.Frame(self, bg=self.colors['bg_panel'])
        card_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Image container (largest part of card) - e-commerce style
        image_container = tk.Frame(card_inner, bg='#F8F8F8', height=220)
        image_container.pack(fill=tk.X, pady=(0, 8))
        image_container.pack_propagate(False)
        
        self.image_label = tk.Label(image_container, text="No Image", 
                                   bg='#F8F8F8', fg=self.colors['text_light'],
                                   font=self.fonts['small'], anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load image if available
        self._load_image()
        
        # Status badge (top of image)
        status_frame = tk.Frame(image_container, bg='#F8F8F8')
        status_frame.place(relx=0, rely=0, x=8, y=8)
        
        status_colors = {
            'In Drawer': self.colors['success'],
            'Laundry': self.colors['warning'],
            'Worn': self.colors['danger']
        }
        status_bg = status_colors.get(self.shirt.status, self.colors['accent'])
        
        status_badge = tk.Label(status_frame, text=self.shirt.status, 
                               bg=status_bg, fg='white',
                               font=('Segoe UI', 8, 'bold'),
                               padx=8, pady=2)
        status_badge.pack()
        
        # Product info container with layout: name/details on left, blue box on right
        info_container = tk.Frame(card_inner, bg=self.colors['bg_panel'])
        info_container.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        # Left side: name and details
        left_info = tk.Frame(info_container, bg=self.colors['bg_panel'])
        left_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Shirt name (truncated if too long)
        name_text = self.shirt.name if len(self.shirt.name) <= 25 else self.shirt.name[:22] + "..."
        name_label = tk.Label(left_info, text=name_text, 
                             bg=self.colors['bg_panel'], fg=self.colors['text'],
                             font=self.fonts['normal'], anchor=tk.W,
                             wraplength=140, justify=tk.LEFT)
        name_label.pack(fill=tk.X, pady=(0, 4))
        
        # Details row (Color | Size)
        details_frame = tk.Frame(left_info, bg=self.colors['bg_panel'])
        details_frame.pack(fill=tk.X)
        
        color_label = tk.Label(details_frame, text=f"● {self.shirt.color}", 
                              bg=self.colors['bg_panel'], fg=self.colors['text_light'],
                              font=self.fonts['small'], anchor=tk.W)
        color_label.pack(side=tk.LEFT)
        
        size_label = tk.Label(details_frame, text=f" | {self.shirt.size}", 
                             bg=self.colors['bg_panel'], fg=self.colors['text_light'],
                             font=self.fonts['small'])
        size_label.pack(side=tk.LEFT)
        
        # Right side: Container with ID, Edit, and Delete buttons
        blue_box = tk.Frame(info_container, bg='white', relief=tk.FLAT, 
                           bd=0, highlightthickness=0)
        blue_box.pack(side=tk.RIGHT, padx=(8, 0))
        blue_box.configure(width=50, height=80)
        blue_box.pack_propagate(False)
        self._blue_box_ref = blue_box  # Store reference for later use
        
        # ID number at top right of blue box
        id_label = tk.Label(blue_box, text=f"#{self.shirt.id}", 
                           bg='white', fg=self.colors['text_light'],
                           font=('Segoe UI', 8), anchor=tk.NE)
        id_label.pack(anchor=tk.NE, padx=4, pady=2)
        
        # Button container in the blue box
        button_container = tk.Frame(blue_box, bg='white')
        button_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Edit button
        if self.on_edit:
            edit_btn = tk.Button(button_container, text="Edit", 
                                command=lambda: self.on_edit(self.shirt),
                                bg='white', fg='#0078D4', 
                                font=('Segoe UI', 7, 'bold'),
                                relief=tk.FLAT, bd=0, cursor='hand2',
                                padx=4, pady=2, activebackground='#E3F2FD',
                                activeforeground='#0078D4')
            edit_btn.pack(fill=tk.X, pady=(0, 2))
            self._button_widgets.append(edit_btn)
        
        # Delete button
        if self.on_delete:
            delete_btn = tk.Button(button_container, text="Delete", 
                                  command=lambda: self.on_delete(self.shirt),
                                  bg='white', fg='#D32F2F', 
                                  font=('Segoe UI', 7, 'bold'),
                                  relief=tk.FLAT, bd=0, cursor='hand2',
                                  padx=4, pady=2, activebackground='#FFEBEE',
                                  activeforeground='#D32F2F')
            delete_btn.pack(fill=tk.X)
            self._button_widgets.append(delete_btn)
    
    def _load_image(self) -> None:
        """Load and display shirt image."""
        image_path = get_image_display_path(self.shirt.image_path)
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                # Resize to fit card (maintain aspect ratio)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.current_image_photo = photo
                self.image_label.configure(image=photo, text="", bg='white')
            except Exception:
                self.image_label.configure(text="Image Error", 
                                         bg='#F8F8F8', fg=self.colors['danger'])
        else:
            # Placeholder image
            self.image_label.configure(text="📷\nNo Image", 
                                     bg='#F8F8F8', fg=self.colors['text_light'],
                                     font=self.fonts['normal'])
    
    def _on_click(self) -> None:
        """Handle card click."""
        if self.on_click:
            self.on_click(self.shirt)
    
    def _on_right_click(self, event) -> None:
        """Handle right-click."""
        if self.on_right_click:
            self.on_right_click(self.shirt, event)
    
    
    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self.is_selected = selected
        if selected:
            self.configure(highlightbackground=self.colors['accent'], 
                          highlightthickness=2, bg=self.colors['accent'])
            # Update all child widgets to match selection
            for widget in self.winfo_children():
                try:
                    widget.configure(bg=self.colors['accent'])
                except:
                    pass
        else:
            self.configure(highlightbackground=self.colors['border'], 
                          highlightthickness=1, bg=self.colors['bg_panel'])
            # Reset child widgets
            for widget in self.winfo_children():
                try:
                    widget.configure(bg=self.colors['bg_panel'])
                except:
                    pass

