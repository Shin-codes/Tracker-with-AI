import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk
from typing import Optional, Dict

# Migrate GUI to use modular src package (shared with CLI/Chatbot)
from src.models import Shirt, STATUSES
from src.storage import load_shirts, save_shirts
from src.inventory_manager import (
    add_shirt as mgr_add_shirt,
    update_status as mgr_update_status,
    delete_shirt as mgr_delete_shirt,
    update_shirt as mgr_update_shirt,
    counts_by_status,
    search_shirts,
    get_statistics,
)
from src.image_utils import save_image_from_path, delete_image, get_image_display_path
from src.gui.components.chatbot_window import ChatbotWindow
from src.gui.components.add_shirt_window import AddShirtWindow
from src.gui.components.edit_shirt_window import EditShirtWindow
from src.gui.components.shirt_card import ShirtCard
from src.gui.components.landing_page import LandingPage


class ShirtInventoryGUI(tk.Tk):
    def __init__(self, show_immediately: bool = True) -> None:
        super().__init__()
        self.title("Shirt Inventory Tracker")
        self.minsize(800, 600)  # Minimum window size
        self.configure(bg="#F5F5F5")  # Light gray background
        
        # Set to maximized/fullscreen on Windows
        try:
            self.state('zoomed')  # Maximized on Windows
        except:
            # Fallback for other platforms or if zoomed doesn't work
            try:
                self.attributes('-zoomed', True)  # Alternative for some systems
            except:
                # Final fallback: use default geometry
                self.geometry("1300x750")
        
        # Hide window initially if not showing immediately (for landing page)
        if not show_immediately:
            self.withdraw()

        # Base dimensions for scaling calculations
        self.base_width = 1300
        self.base_height = 750
        
        # Responsive state - update after window is shown/maximized
        self.update_idletasks()  # Update to get actual window size
        try:
            self.current_width = self.winfo_width()
            self.current_height = self.winfo_height()
        except:
            # Fallback if window not yet visible
            self.current_width = 1300
            self.current_height = 750
        self.prev_width = self.current_width
        self.prev_height = self.current_height
        self.layout_mode = "medium"  # small, medium, large
        self.prev_layout_mode = None
        
        # DPI scaling factor
        self.dpi_scale = 1.0
        try:
            # Get system DPI scaling
            self.dpi_scale = self.tk.call('tk', 'scaling')
        except:
            pass

        # Color scheme - Using custom palette
        # Deep purple: #450693, Vibrant purple: #8C00FF, Hot pink: #FF3F7F, Golden yellow: #FFC400
        self.colors = {
            'bg_main': '#F5F5F5',  # Light gray background
            'bg_panel': '#FFFFFF',  # White panels
            'bg_entry': '#FAFAFA',  # Very light gray for entries
            'accent': '#8C00FF',  # Vibrant purple - primary accent
            'accent_hover': '#FF3F7F',  # Hot pink - hover states
            'accent_dark': '#450693',  # Deep purple - darker accents
            'success': '#FFC400',  # Golden yellow - success states
            'danger': '#FF3F7F',  # Hot pink - danger/delete actions
            'warning': '#FFC400',  # Golden yellow - warnings
            'text': '#333333',  # Dark gray text
            'text_light': '#666666',  # Medium gray text
            'border': '#E0E0E0',  # Light gray borders
        }

        # Base font sizes (will be scaled)
        self.base_fonts = {
            'title': 16,
            'heading': 11,
            'normal': 10,
            'small': 9,
            'button': 10,
        }

        # In-memory data (shared with CLI/Chatbot)
        self.shirts = load_shirts()
        self.current_shirt = None
        self.search_filter = ""
        self.header_logo = None  # Store header logo reference
        
        # Performance optimization: cache and debounce
        self.search_debounce_id = None
        self.stats_cache = None  # Cache for statistics
        self.stats_cache_valid = False  # Flag to invalidate cache

        # Configure style
        self.fonts = self._get_scaled_fonts()
        self._configure_styles()

        # Build UI
        self._build_widgets()
        self._refresh_all()
        
        # Bind resize event for responsive behavior
        self.bind("<Configure>", self._on_window_resize)
        
        # Initial layout calculation
        self._update_layout()
    
    
    def _get_scaled_fonts(self) -> Dict[str, tuple]:
        """Calculate scaled fonts based on window size and DPI."""
        scale_factor = self.current_width / self.base_width
        # Clamp scale factor between 0.8 and 1.4 for readability
        scale_factor = max(0.8, min(1.4, scale_factor))
        # Apply DPI scaling
        scale_factor *= self.dpi_scale
        
        return {
            'title': ('Segoe UI', int(self.base_fonts['title'] * scale_factor), 'bold'),
            'heading': ('Segoe UI', int(self.base_fonts['heading'] * scale_factor), 'bold'),
            'normal': ('Segoe UI', int(self.base_fonts['normal'] * scale_factor)),
            'small': ('Segoe UI', int(self.base_fonts['small'] * scale_factor)),
            'button': ('Segoe UI', int(self.base_fonts['button'] * scale_factor), 'bold'),
        }
    
    def _scale_value(self, base_value: int) -> int:
        """Scale a value proportionally based on window width and DPI."""
        scale_factor = self.current_width / self.base_width
        scale_factor = max(0.8, min(1.4, scale_factor))
        scale_factor *= self.dpi_scale
        return int(base_value * scale_factor)
    
    def _scale_padding(self, base_padding: int) -> int:
        """Scale padding values based on window size."""
        scale_factor = self.current_width / self.base_width
        scale_factor = max(0.7, min(1.3, scale_factor))
        return int(base_padding * scale_factor)
    
    def _configure_styles(self) -> None:
        """Configure ttk styles for a modern, light theme."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Get current scaled fonts
        fonts = self._get_scaled_fonts()
        
        # Configure colors
        style.configure('TFrame', background=self.colors['bg_main'])
        style.configure('TLabelFrame', background=self.colors['bg_panel'], borderwidth=1, relief=tk.FLAT)
        style.configure('TLabelFrame.Label', background=self.colors['bg_panel'], foreground=self.colors['text'], font=fonts['heading'])
        style.configure('TLabel', background=self.colors['bg_main'], foreground=self.colors['text'], font=fonts['normal'])
        style.configure('TEntry', fieldbackground=self.colors['bg_entry'], borderwidth=1, relief=tk.SOLID, padding=(8, 10))
        style.configure('TButton', font=fonts['button'], padding=(10, 5))
        style.configure('TCombobox', fieldbackground=self.colors['bg_entry'], borderwidth=1)
        style.configure('TNotebook', background=self.colors['bg_main'], borderwidth=0)
        style.configure('TNotebook.Tab', background=self.colors['bg_panel'], padding=[20, 10], font=fonts['normal'])
        
        # Custom button styles
        style.map('TButton',
                  background=[('active', self.colors['accent_hover']), ('!active', self.colors['accent'])],
                  foreground=[('active', 'white'), ('!active', 'white')])
        
        # Primary button style
        style.configure('Primary.TButton', background=self.colors['accent'], foreground='white')
        style.map('Primary.TButton',
                  background=[('active', self.colors['accent_hover']), ('!active', self.colors['accent'])])
        
        # Success button style
        style.configure('Success.TButton', background=self.colors['success'], foreground='white')
        style.map('Success.TButton',
                  background=[('active', self.colors['accent_dark']), ('!active', self.colors['success'])])
        
        # Danger button style
        style.configure('Danger.TButton', background=self.colors['danger'], foreground='white')
        style.map('Danger.TButton',
                  background=[('active', self.colors['accent_dark']), ('!active', self.colors['danger'])])

    # ----- UI Construction -----
    def _build_widgets(self) -> None:
        # Header
        header_frame = tk.Frame(self, bg=self.colors['bg_panel'], height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Try to load logo for header
        logo_path = _get_logo_path()
        logo_container = tk.Frame(header_frame, bg=self.colors['bg_panel'])
        logo_container.pack(side=tk.LEFT, padx=20, pady=10)
        
        if logo_path and os.path.exists(logo_path):
            try:
                # Load small logo for header (40x40px)
                img = Image.open(logo_path)
                img.thumbnail((40, 40), Image.Resampling.LANCZOS)
                header_logo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(logo_container, image=header_logo,
                                     bg=self.colors['bg_panel'])
                logo_label.image = header_logo  # Keep reference to prevent garbage collection
                logo_label.pack(side=tk.LEFT, padx=(0, 10))
            except Exception as e:
                # Fallback to emoji if image load fails
                import traceback
                print(f"Logo loading error: {e}")
                traceback.print_exc()
                logo_label = tk.Label(logo_container, text="👕", font=('Segoe UI', 24),
                                    bg=self.colors['bg_panel'], fg=self.colors['accent'])
                logo_label.pack(side=tk.LEFT, padx=(0, 10))
        else:
            # Fallback to emoji if no logo file
            if not logo_path:
                print(f"Logo path not found. Checked in: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')}")
            logo_label = tk.Label(logo_container, text="👕", font=('Segoe UI', 24),
                                bg=self.colors['bg_panel'], fg=self.colors['accent'])
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = tk.Label(header_frame, text="Shirt Inventory Tracker", 
                               font=self.fonts['title'], bg=self.colors['bg_panel'], 
                               fg=self.colors['text'])
        title_label.pack(side=tk.LEFT, pady=15)
        
        # Right side of header: Statistics and Search bar
        header_right = tk.Frame(header_frame, bg=self.colors['bg_panel'])
        header_right.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # Statistics button (left of search)
        stats_btn = ttk.Button(header_right, text="📊 Statistics", 
                               command=self._show_statistics, style='Primary.TButton', width=12)
        stats_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Search section (right side)
        search_frame = tk.Frame(header_right, bg=self.colors['bg_panel'])
        search_frame.pack(side=tk.LEFT)
        
        tk.Label(search_frame, text="🔍", font=self.fonts['normal'], 
                bg=self.colors['bg_panel'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 6))
        self.search_entry = ttk.Entry(search_frame, width=25, font=self.fonts['normal'])
        self.search_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_debounced())
        ttk.Button(search_frame, text="Clear", command=self._clear_search, 
                  style='TButton', width=8).pack(side=tk.LEFT)
        
        # Main container with sidebar and content
        main_container = tk.Frame(self, bg=self.colors['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(15, 10))
        
        # Left sidebar navbar
        self.sidebar = tk.Frame(main_container, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=1, width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.sidebar.pack_propagate(False)
        self.sidebar.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        # Sidebar title
        sidebar_title = tk.Label(self.sidebar, text="Filter by Status", font=self.fonts['heading'],
                                bg=self.colors['bg_panel'], fg=self.colors['text'])
        sidebar_title.pack(padx=15, pady=(15, 10))
        
        # Separator line
        separator = tk.Frame(self.sidebar, bg=self.colors['border'], height=1)
        separator.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Count labels in sidebar (vertical stack)
        self.count_labels = {}
        self.label_frames = {}  # Store frames for styling
        self.filter_status = None  # Track current filter
        for status in STATUSES:
            # Create a frame for each label to make it more clickable
            label_frame = tk.Frame(self.sidebar, bg=self.colors['bg_panel'], relief=tk.FLAT)
            label_frame.pack(fill=tk.X, padx=10, pady=5)
            self.label_frames[status] = label_frame
            
            # Make count labels clickable
            lbl = tk.Label(label_frame, text=f"{status}: 0", font=self.fonts['normal'],
                          bg=self.colors['bg_panel'], fg=self.colors['text'],
                          cursor='hand2', anchor='w', padx=10, pady=8)
            lbl.pack(fill=tk.X)
            lbl.bind("<Button-1>", lambda e, s=status: self._filter_by_status(s))
            
            # Add hover effect
            def on_enter(e, l=lbl, f=label_frame, s=status):
                if self.filter_status != s:
                    l.configure(bg=self.colors['bg_entry'])
                    f.configure(bg=self.colors['bg_entry'])
            
            def on_leave(e, l=lbl, f=label_frame, s=status):
                if self.filter_status != s:
                    l.configure(bg=self.colors['bg_panel'])
                    f.configure(bg=self.colors['bg_panel'])
            
            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
            
            self.count_labels[status] = lbl
        
        # Main content area - Cards grid
        self.content = tk.Frame(main_container, bg=self.colors['bg_main'])
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Cards container with header
        cards_container = tk.Frame(self.content, bg=self.colors['bg_panel'])
        cards_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with "Add New Shirt" button
        cards_header = tk.Frame(cards_container, bg=self.colors['bg_panel'], height=40)
        cards_header.pack(fill=tk.X, padx=10, pady=(10, 0))
        cards_header.pack_propagate(False)
        
        # Add New Shirt button in upper right corner
        btn_add_shirt = ttk.Button(cards_header, text="➕ Add New Shirt", 
                                   command=self._open_add_shirt_window,
                                   style='Success.TButton', width=18)
        btn_add_shirt.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Scrollable canvas for cards grid
        cards_frame = tk.Frame(cards_container, bg=self.colors['bg_panel'])
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Canvas and scrollbar
        self.cards_canvas = tk.Canvas(cards_frame, bg=self.colors['bg_main'], highlightthickness=0)
        cards_scrollbar = ttk.Scrollbar(cards_frame, orient=tk.VERTICAL, command=self.cards_canvas.yview)
        
        # Container frame for cards (inside canvas)
        self.cards_grid_frame = tk.Frame(self.cards_canvas, bg=self.colors['bg_main'])
        self.cards_canvas_window = self.cards_canvas.create_window((0, 0), window=self.cards_grid_frame, anchor='nw')
        
        # Configure scrolling
        def configure_cards_scroll(event=None):
            self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox('all'))
            # Update canvas window width
            canvas_width = event.width if event else self.cards_canvas.winfo_width()
            self.cards_canvas.itemconfig(self.cards_canvas_window, width=canvas_width)
        
        self.cards_grid_frame.bind('<Configure>', configure_cards_scroll)
        self.cards_canvas.bind('<Configure>', configure_cards_scroll)
        
        self.cards_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cards_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cards_canvas.configure(yscrollcommand=cards_scrollbar.set)
        
        # Mousewheel scrolling
        def on_mousewheel(event):
            self.cards_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.cards_canvas.bind("<Enter>", lambda e: self.cards_canvas.bind_all("<MouseWheel>", on_mousewheel))
        self.cards_canvas.bind("<Leave>", lambda e: self.cards_canvas.unbind_all("<MouseWheel>"))
        
        # Store card references
        self.shirt_cards = {}  # shirt_id -> ShirtCard widget
        self.selected_card = None

        # Create chatbot component
        self.chatbot = ChatbotWindow(self, self.shirts, self.colors, self.refresh_callback)
        
        # Track open windows
        self.add_window = None
        self.edit_window = None

    # ----- Context Menu -----

    # ----- Window Openers -----
    def _open_add_shirt_window(self) -> None:
        """Open the Add New Shirt window."""
        if self.add_window is None or not self.add_window.winfo_exists():
            self.add_window = AddShirtWindow(self, self.shirts, self.refresh_callback, 
                                             self.colors, self.fonts)
        else:
            self.add_window.lift()
            self.add_window.focus()
    
    def _open_edit_shirt_window(self, status=None) -> None:
        """Open the Edit Shirt window for selected shirt."""
        shirt = self._get_selected_shirt()
        if not shirt:
            messagebox.showinfo("No Selection", "Please select a shirt to edit.")
            return
        
        if self.edit_window is None or not self.edit_window.winfo_exists():
            self.edit_window = EditShirtWindow(self, shirt, self.shirts, self.refresh_callback,
                                              self.colors, self.fonts)
        else:
            self.edit_window.lift()
            self.edit_window.focus()
            # Update with new selection if different shirt selected
            self.edit_window.load_shirt(shirt)
    
    def refresh_callback(self) -> None:
        """Callback to refresh main window after changes."""
        self._refresh_all()
        save_shirts(self.shirts)

    # ----- Helpers -----
    def _refresh_all(self) -> None:
        self._refresh_lists()
        self._refresh_counts()
        self.stats_cache_valid = False  # Invalidate stats cache

    def _on_search_debounced(self) -> None:
        """Debounced search to avoid excessive filtering."""
        if self.search_debounce_id:
            self.after_cancel(self.search_debounce_id)
        self.search_debounce_id = self.after(300, self._on_search)  # 300ms delay
    
    def _refresh_lists(self) -> None:
        # Clear all existing cards
        for card in self.shirt_cards.values():
            card.destroy()
        self.shirt_cards.clear()
        self.selected_card = None

        # Apply search filter
        display_shirts = self.shirts
        if self.search_filter:
            display_shirts = search_shirts(self.shirts, self.search_filter)

        # Apply status filter if set
        if self.filter_status:
            display_shirts = [s for s in display_shirts if s.status == self.filter_status]

        # Calculate columns based on window width
        card_width = 220  # Fixed card width
        available_width = max(self.current_width - 280, 600)  # Subtract sidebar and padding
        columns = max(2, int(available_width / (card_width + 20)))  # At least 2 columns
        
        # Create cards in grid
        row = 0
        col = 0
        
        for s in display_shirts:
            # Create card
            card = ShirtCard(self.cards_grid_frame, s, self.colors, self.fonts,
                           on_click=self._on_card_click,
                           on_right_click=self._on_card_right_click,
                           on_edit=self._open_edit_shirt_window_from_card,
                           on_delete=self._delete_shirt_from_card)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            self.shirt_cards[s.id] = card
            
            # Configure grid weights (for equal spacing)
            self.cards_grid_frame.grid_columnconfigure(col, weight=1)
            
            # Move to next position
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
        # Update canvas scroll region
        self.cards_canvas.update_idletasks()
        self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox('all'))
    
    def _on_card_click(self, shirt: Shirt) -> None:
        """Handle card click."""
        # Deselect previous card
        if self.selected_card and self.selected_card in self.shirt_cards.values():
            self.selected_card.set_selected(False)
        
        # Select clicked card
        if shirt.id in self.shirt_cards:
            self.selected_card = self.shirt_cards[shirt.id]
            self.selected_card.set_selected(True)
            self.current_shirt = shirt
    
    def _on_card_right_click(self, shirt: Shirt, event) -> None:
        """Handle card right-click (show context menu)."""
        # Select the card first
        self._on_card_click(shirt)
        # Show context menu
        self._show_context_menu_card(shirt, event)
    
    def _show_context_menu_card(self, shirt: Shirt, event) -> None:
        """Show context menu for card."""
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="✏️ Edit Shirt", 
                               command=lambda: self._open_edit_shirt_window_from_card(shirt))
        context_menu.add_command(label="🗑️ Delete Shirt", 
                               command=lambda: self._delete_shirt_from_card(shirt))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _open_edit_shirt_window_from_card(self, shirt: Shirt) -> None:
        """Open edit window from card context menu."""
        if self.edit_window is None or not self.edit_window.winfo_exists():
            self.edit_window = EditShirtWindow(self, shirt, self.shirts, self.refresh_callback,
                                              self.colors, self.fonts)
        else:
            self.edit_window.lift()
            self.edit_window.focus()
            self.edit_window.load_shirt(shirt)
    
    def _delete_shirt_from_card(self, shirt: Shirt) -> None:
        """Delete shirt from card context menu."""
        self.current_shirt = shirt
        self._on_delete()
    
    def _filter_by_status(self, status: str) -> None:
        """Filter shirts by status when count label is clicked."""
        if self.filter_status == status:
            # Toggle: if already filtered by this status, show all
            self.filter_status = None
        else:
            self.filter_status = status
        
        # Update visual feedback on count labels
        self._update_count_labels_style()
        self._refresh_lists()
    
    def _update_count_labels_style(self) -> None:
        """Update count label styles to show active filter."""
        for status, lbl in self.count_labels.items():
            label_frame = self.label_frames[status]
            if self.filter_status == status:
                # Highlight active filter
                lbl.configure(bg=self.colors['accent'], fg='white', font=self.fonts['heading'])
                label_frame.configure(bg=self.colors['accent'])
            else:
                # Normal style
                lbl.configure(bg=self.colors['bg_panel'], fg=self.colors['text'], font=self.fonts['normal'])
                label_frame.configure(bg=self.colors['bg_panel'])

    def _refresh_counts(self) -> None:
        counts = counts_by_status(self.shirts)
        for status in STATUSES:
            self.count_labels[status].configure(text=f"{status}: {counts.get(status, 0)}")

    def _get_current_status_tab(self) -> str:
        """Get current filter status, or return None for all."""
        return self.filter_status

    def _get_selected_shirt(self) -> Shirt | None:
        """Get currently selected shirt."""
        return self.current_shirt
    
    def _on_window_resize(self, event=None) -> None:
        """Handle window resize events for responsive layout."""
        if event and event.widget == self:
            self.current_width = event.width
            self.current_height = event.height
            # Only update layout if size actually changed (not just position)
            if self.current_width != self.prev_width or self.current_height != self.prev_height:
                self.prev_width = self.current_width
                self.prev_height = self.current_height
                self._update_layout()
            # Update chatbot window position if visible
            if hasattr(self, 'chatbot'):
                self.chatbot.update_position()
    
    def _determine_layout_mode(self) -> str:
        """Determine layout mode based on window width."""
        if self.current_width < 1000:
            return "small"
        elif self.current_width > 1400:
            return "large"
        else:
            return "medium"
    
    def _update_layout(self) -> None:
        """Update layout based on current window size."""
        # Update layout mode
        new_mode = self._determine_layout_mode()
        self.prev_layout_mode = self.layout_mode
        self.layout_mode = new_mode
        
        # Refresh cards grid on resize to adjust columns
        if hasattr(self, 'cards_grid_frame'):
            self._refresh_lists()
        
        # Chatbot window position is handled separately
        
        # Update fonts dynamically
        self._update_fonts()
    
    def _update_fonts(self) -> None:
        """Update all font sizes based on current window size."""
        fonts = self._get_scaled_fonts()
        self.fonts = fonts
        
        # Update widget fonts if they exist
        if hasattr(self, 'count_labels'):
            for lbl in self.count_labels.values():
                lbl.configure(font=fonts['normal'])
        
        # Update entry and listbox fonts
        if hasattr(self, 'search_entry'):
            self.search_entry.configure(font=fonts['normal'])
        if hasattr(self, 'chat_input'):
            self.chat_input.configure(font=fonts['normal'])
        if hasattr(self, 'main_treeview'):
            # Treeview font is configured via style, already handled in _configure_styles
            pass
        
        # Reconfigure styles with new fonts
        self._configure_styles()
    
    def _on_search(self) -> None:
        """Handle search input changes."""
        self.search_filter = self.search_entry.get().strip()
        self._refresh_lists()
    
    def _clear_search(self) -> None:
        """Clear search filter."""
        self.search_entry.delete(0, tk.END)
        self.search_filter = ""
        self._refresh_lists()
    
    
    def _show_statistics(self) -> None:
        """Display statistics window (with caching)."""
        # Use cached stats if available
        if not self.stats_cache_valid or self.stats_cache is None:
            self.stats_cache = get_statistics(self.shirts)
            self.stats_cache_valid = True
        
        stats = self.stats_cache
        
        stats_window = tk.Toplevel(self)
        stats_window.title("Inventory Statistics")
        stats_window.geometry("550x500")
        stats_window.configure(bg=self.colors['bg_main'])
        
        # Header
        header = tk.Frame(stats_window, bg=self.colors['bg_panel'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📊 Inventory Statistics", font=self.fonts['title'],
                bg=self.colors['bg_panel'], fg=self.colors['text']).pack(padx=20, pady=12)
        
        # Content
        content_frame = tk.Frame(stats_window, bg=self.colors['bg_panel'], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        text_widget = tk.Text(content_frame, wrap=tk.WORD, padx=15, pady=15,
                            font=self.fonts['normal'], bg=self.colors['bg_entry'],
                            fg=self.colors['text'], relief=tk.FLAT, bd=1,
                            highlightthickness=1, highlightbackground=self.colors['border'])
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        stats_text = "📊 INVENTORY STATISTICS\n"
        stats_text += "=" * 50 + "\n\n"
        stats_text += f"Total Shirts: {stats['total']}\n\n"
        
        stats_text += "By Status:\n"
        for status, count in stats['by_status'].items():
            stats_text += f"  • {status}: {count}\n"
        
        stats_text += "\nBy Color:\n"
        for color, count in sorted(stats['by_color'].items()):
            stats_text += f"  • {color}: {count}\n"
        
        stats_text += "\nBy Size:\n"
        for size, count in sorted(stats['by_size'].items()):
            stats_text += f"  • {size}: {count}\n"
        
        stats_text += f"\nShirts with Images: {stats['with_images']}\n"
        stats_text += f"Shirts without Images: {stats['total'] - stats['with_images']}\n"
        
        text_widget.insert("1.0", stats_text)
        text_widget.configure(state=tk.DISABLED)
        
        btn_frame = tk.Frame(stats_window, bg=self.colors['bg_main'])
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Button(btn_frame, text="Close", command=stats_window.destroy,
                  style='Primary.TButton', width=15).pack()
    
    # ----- Event Handlers -----

    def _on_delete(self) -> None:
        shirt = self._get_selected_shirt()
        if not shirt:
            messagebox.showinfo("No Selection", "Please select a shirt to delete.")
            return
        resp = messagebox.askyesno(
            "Confirm Delete",
            f"Delete #{shirt.id} - {shirt.name}?\n\nThis will also delete the associated image if it exists.",
            icon="warning",
        )
        if not resp:
            return
        try:
            # Delete associated image
            if shirt.image_path:
                delete_image(shirt.image_path)
            
            # Clear card if it exists
            if shirt.id in self.shirt_cards:
                self.shirt_cards[shirt.id].destroy()
                del self.shirt_cards[shirt.id]
            
            mgr_delete_shirt(self.shirts, shirt.id)
            save_shirts(self.shirts)
            self.current_shirt = None
            self._refresh_all()
            messagebox.showinfo("Success", "Shirt deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def _get_logo_path() -> Optional[str]:
    """Helper function to get path to logo image file if it exists."""
    # Get the directory where this file is located
    try:
        # __file__ might be relative or absolute depending on how script is run
        current_file = os.path.abspath(__file__)
    except NameError:
        # If __file__ doesn't exist, use current working directory
        current_file = os.path.abspath(os.path.join(os.getcwd(), "shirt_inventory_gui.py"))
    
    current_dir = os.path.dirname(current_file)
    
    # data directory should be at the same level as shirt_inventory_gui.py
    data_dir = os.path.join(current_dir, "data")
    
    # Check for logo files in data directory
    logo_names = ["logo.png", "logo.jpg", "logo.jpeg", "logo.gif", "wardrobe.png", "wardrobe.jpg"]
    
    for logo_name in logo_names:
        logo_path = os.path.join(data_dir, logo_name)
        if os.path.exists(logo_path) and os.path.isfile(logo_path):
            return logo_path
    
    return None


def main() -> None:
    # Color scheme for landing page
    colors = {
        'bg_main': '#F5F5F5',
        'accent': '#8C00FF',
        'text': '#333333',
        'text_light': '#666666',
    }
    
    # Create main app (hidden initially)
    app = ShirtInventoryGUI(show_immediately=False)
    
    # Show landing page first
    def launch_main_app():
        app.deiconify()  # Show main app
        # Set to maximized/fullscreen after showing
        try:
            app.state('zoomed')  # Maximized on Windows
        except:
            try:
                app.attributes('-zoomed', True)  # Alternative for some systems
            except:
                pass
        # Update window dimensions after showing (for maximized state)
        app.update_idletasks()
        try:
            app.current_width = app.winfo_width()
            app.current_height = app.winfo_height()
            app.prev_width = app.current_width
            app.prev_height = app.current_height
        except:
            pass
        app.mainloop()
    
    landing = LandingPage(launch_main_app, colors, duration_ms=2000)
    landing.mainloop()


if __name__ == "__main__":
    main()
