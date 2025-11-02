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
from src.chatbot import process_message as chatbot_process
from src.image_utils import save_image_from_path, delete_image, get_image_display_path


class ShirtInventoryGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Shirt Inventory Tracker")
        self.geometry("1300x750")
        self.minsize(800, 600)  # Minimum window size
        self.configure(bg="#F5F5F5")  # Light gray background

        # Base dimensions for scaling calculations
        self.base_width = 1300
        self.base_height = 750
        
        # Responsive state
        self.current_width = 1300
        self.current_height = 750
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
        self.current_image_photo = None
        self.search_filter = ""
        self.header_logo = None  # Store header logo reference
        
        # Performance optimization: cache and debounce
        self.search_debounce_id = None
        self.thumbnail_cache = {}  # Cache for image thumbnails
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
    
    def _create_floating_chatbot_button(self) -> None:
        """Create a floating chatbot button at the bottom right of the window."""
        # Floating button container (positioned absolutely)
        self.floating_button_frame = tk.Frame(self, bg='', highlightthickness=0)
        self.floating_button_frame.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)
        
        # Create circular/rounded button
        self.floating_button = tk.Button(
            self.floating_button_frame,
            text="💬",
            font=('Segoe UI', 20),
            bg=self.colors['accent'],
            fg='white',
            activebackground=self.colors['accent_hover'],
            activeforeground='white',
            relief=tk.FLAT,
            borderwidth=0,
            cursor='hand2',
            width=3,
            height=1,
            command=self._toggle_chatbot_overlay
        )
        self.floating_button.pack()
        
        # Add hover effect
        def on_enter(e):
            self.floating_button.configure(bg=self.colors['accent_hover'])
        
        def on_leave(e):
            self.floating_button.configure(bg=self.colors['accent'])
        
        self.floating_button.bind("<Enter>", on_enter)
        self.floating_button.bind("<Leave>", on_leave)
    
    def _create_chatbot_overlay(self) -> None:
        """Create the chatbot overlay panel that appears on top of content."""
        # Create overlay frame (initially hidden)
        self.chatbot_overlay = tk.Frame(self, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=0)
        # Add shadow/border effect
        self.chatbot_overlay.configure(highlightbackground=self.colors['border'], highlightthickness=2)
        
        # Header with close button
        header_overlay = tk.Frame(self.chatbot_overlay, bg=self.colors['bg_panel'], height=50)
        header_overlay.pack(fill=tk.X)
        header_overlay.pack_propagate(False)
        
        title_label = tk.Label(header_overlay, text="💬 Chatbot Assistant", 
                              font=self.fonts['heading'], bg=self.colors['bg_panel'], 
                              fg=self.colors['text'])
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Close button
        close_btn = tk.Button(header_overlay, text="✕", font=('Segoe UI', 16),
                             bg=self.colors['bg_panel'], fg=self.colors['text_light'],
                             activebackground=self.colors['danger'], activeforeground='white',
                             relief=tk.FLAT, borderwidth=0, cursor='hand2',
                             width=3, height=1, command=self._close_chatbot_overlay)
        close_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # Chat container
        bot = tk.Frame(self.chatbot_overlay, bg=self.colors['bg_panel'])
        bot.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Chat log with scrollbar
        log_frame = tk.Frame(bot, bg=self.colors['bg_panel'])
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_log = tk.Text(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD,
                               font=self.fonts['small'], bg=self.colors['bg_entry'],
                               fg=self.colors['text'], relief=tk.SOLID, bd=1,
                               padx=8, pady=8, highlightthickness=0)
        self.chat_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.chat_log.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_log.configure(yscrollcommand=log_scroll.set)

        # Input row
        input_frame = tk.Frame(bot, bg=self.colors['bg_panel'])
        input_frame.pack(fill=tk.X)
        
        # Use tk.Entry for better control over text display
        self.chat_input = tk.Entry(input_frame, 
                                   font=self.fonts['normal'],
                                   bg=self.colors['bg_entry'],
                                   fg=self.colors['text'],
                                   relief=tk.SOLID,
                                   bd=1,
                                   highlightthickness=1,
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'],
                                   insertbackground=self.colors['text'],
                                   borderwidth=1)
        self.chat_input.configure(insertwidth=2)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)
        send_btn = ttk.Button(input_frame, text="Send", command=self._on_chat_send,
                             style='Primary.TButton', width=10)
        send_btn.pack(side=tk.LEFT)
        # Enter key binding
        self.chat_input.bind("<Return>", lambda e: self._on_chat_send())
        
        # Initially hide overlay
        self.chatbot_overlay.place_forget()
    
    def _toggle_chatbot_overlay(self) -> None:
        """Toggle the chatbot overlay visibility."""
        if self.chatbot_overlay_visible:
            self._close_chatbot_overlay()
        else:
            self._show_chatbot_overlay()
    
    def _show_chatbot_overlay(self) -> None:
        """Show the chatbot overlay."""
        self.chatbot_overlay_visible = True
        # Position overlay at bottom half of window
        self.chatbot_overlay.place(relx=0, rely=0.5, relwidth=1.0, relheight=0.5, anchor='sw')
        # Bring overlay to front and ensure floating button stays on top
        self.chatbot_overlay.lift()
        self.floating_button_frame.lift()  # Keep button on top
        self.floating_button.configure(text="💬", bg=self.colors['success'])  # Indicate active state
    
    def _close_chatbot_overlay(self) -> None:
        """Close/hide the chatbot overlay."""
        self.chatbot_overlay_visible = False
        self.chatbot_overlay.place_forget()
        self.floating_button.configure(text="💬", bg=self.colors['accent'])  # Reset button state
    
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
        
        # Top: Counts display
        top_frame = tk.Frame(self, bg=self.colors['bg_main'])
        top_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        # Counts display
        counts_container = tk.Frame(top_frame, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=1)
        counts_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
        counts_container.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        counts_frame = tk.Frame(counts_container, bg=self.colors['bg_panel'])
        counts_frame.pack(padx=15, pady=8)
        
        self.count_labels = {}
        for i, status in enumerate(STATUSES):
            lbl = tk.Label(counts_frame, text=f"{status}: 0", font=self.fonts['normal'],
                          bg=self.colors['bg_panel'], fg=self.colors['text'])
            lbl.pack(side=tk.LEFT, padx=(0, 20))
            self.count_labels[status] = lbl
        
        # Separator
        tk.Label(counts_frame, text="|", font=self.fonts['normal'],
                bg=self.colors['bg_panel'], fg=self.colors['text_light']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.total_label = tk.Label(counts_frame, text="Total: 0", font=self.fonts['heading'],
                                    bg=self.colors['bg_panel'], fg=self.colors['accent'])
        self.total_label.pack(side=tk.LEFT)

        # Main scrollable content area
        # Create main canvas with scrollbar for scrolling the entire window
        main_scroll_frame = tk.Frame(self, bg=self.colors['bg_main'])
        main_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        main_canvas = tk.Canvas(main_scroll_frame, bg=self.colors['bg_main'], highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(main_scroll_frame, orient=tk.VERTICAL, command=main_canvas.yview)
        
        # Main content frame that will be scrolled
        self.content = tk.Frame(main_canvas, bg=self.colors['bg_main'])
        
        # Configure scrolling
        def configure_main_scroll(event=None):
            main_canvas.configure(scrollregion=main_canvas.bbox('all'))
        
        canvas_window = main_canvas.create_window((0, 0), window=self.content, anchor='nw')
        
        def configure_main_canvas_width(event):
            canvas_width = event.width
            main_canvas.itemconfig(canvas_window, width=canvas_width)
        
        main_canvas.bind('<Configure>', configure_main_canvas_width)
        self.content.bind('<Configure>', configure_main_scroll)
        
        # Pack canvas and scrollbar
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Mousewheel scrolling
        def on_main_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def on_main_canvas_enter(event):
            main_canvas.bind_all("<MouseWheel>", on_main_mousewheel)
        
        def on_main_canvas_leave(event):
            main_canvas.unbind_all("<MouseWheel>")
        
        main_canvas.bind("<Enter>", on_main_canvas_enter)
        main_canvas.bind("<Leave>", on_main_canvas_leave)
        
        self.main_canvas = main_canvas  # Store reference

        # Add padding container for content
        content_padding = tk.Frame(self.content, bg=self.colors['bg_main'])
        content_padding.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Notebook with tabs
        self.left_panel = tk.Frame(content_padding, bg=self.colors['bg_main'])
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        self.notebook = ttk.Notebook(self.left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.listboxes = {}
        for status in STATUSES:
            frame = tk.Frame(self.notebook, bg=self.colors['bg_panel'])
            self.notebook.add(frame, text=f"  {status}  ")

            # Listbox with better styling
            listbox_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            listbox = tk.Listbox(listbox_frame, height=20, font=self.fonts['normal'],
                                bg=self.colors['bg_entry'], fg=self.colors['text'],
                                selectbackground=self.colors['accent'], 
                                selectforeground='white',
                                activestyle='none', borderwidth=1, relief=tk.SOLID,
                                highlightthickness=0)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            listbox.bind("<<ListboxSelect>>", lambda e, s=status: self._on_shirt_select())
            
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.configure(yscrollcommand=scrollbar.set)

            self.listboxes[status] = listbox

        # Right-side: Actions + Form with scrollbar
        self.right_container = tk.Frame(content_padding, bg=self.colors['bg_main'])
        self.right_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))

        # Create canvas and scrollbar for scrolling
        self.right_canvas = tk.Canvas(self.right_container, bg=self.colors['bg_main'], highlightthickness=0)
        self.right_scrollbar = ttk.Scrollbar(self.right_container, orient=tk.VERTICAL, command=self.right_canvas.yview)
        
        # Inner frame that holds all content
        right = tk.Frame(self.right_canvas, bg=self.colors['bg_main'])
        
        # Configure canvas scrolling
        def configure_scroll_region(event=None):
            self.right_canvas.configure(scrollregion=self.right_canvas.bbox('all'))
        
        self.canvas_window = self.right_canvas.create_window((0, 0), window=right, anchor='nw')
        
        def configure_canvas_width(event):
            canvas_width = event.width
            self.right_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.right_canvas.bind('<Configure>', configure_canvas_width)
        right.bind('<Configure>', configure_scroll_region)
        
        # Pack canvas and scrollbar
        self.right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Connect scrollbar to canvas
        self.right_canvas.configure(yscrollcommand=self.right_scrollbar.set)
        
        # Mousewheel scrolling (Windows)
        def on_mousewheel(event):
            self.right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def on_canvas_enter(event):
            self.right_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def on_canvas_leave(event):
            self.right_canvas.unbind_all("<MouseWheel>")
        
        self.right_canvas.bind("<Enter>", on_canvas_enter)
        self.right_canvas.bind("<Leave>", on_canvas_leave)

        # Image display area
        image_container = tk.Frame(right, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=1)
        image_container.pack(fill=tk.X, pady=(0, 15))
        image_container.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        tk.Label(image_container, text="🖼️ Shirt Image", font=self.fonts['heading'],
                bg=self.colors['bg_panel'], fg=self.colors['text']).pack(anchor=tk.W, padx=15, pady=(10, 5))
        
        image_inner = tk.Frame(image_container, bg=self.colors['bg_entry'], relief=tk.FLAT)
        image_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.image_label = tk.Label(image_inner, text="No image", anchor=tk.CENTER,
                                    bg=self.colors['bg_entry'], fg=self.colors['text_light'],
                                    font=self.fonts['normal'], relief=tk.FLAT, bd=1,
                                    width=25, height=10)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add form
        form_container = tk.Frame(right, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=1)
        form_container.pack(fill=tk.X, pady=(0, 15))
        form_container.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        tk.Label(form_container, text="➕ Add New Shirt", font=self.fonts['heading'],
                bg=self.colors['bg_panel'], fg=self.colors['text']).pack(anchor=tk.W, padx=15, pady=(12, 8))
        
        form = tk.Frame(form_container, bg=self.colors['bg_panel'])
        form.pack(fill=tk.X, padx=15, pady=(0, 15))

        tk.Label(form, text="Name", font=self.fonts['small'], bg=self.colors['bg_panel'], 
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_name = ttk.Entry(form, font=self.fonts['normal'])
        self.entry_name.pack(fill=tk.X, pady=(0, 10))

        tk.Label(form, text="Color", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_color = ttk.Entry(form, font=self.fonts['normal'])
        self.entry_color.pack(fill=tk.X, pady=(0, 10))

        tk.Label(form, text="Size", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_size = ttk.Entry(form, font=self.fonts['normal'])
        self.entry_size.pack(fill=tk.X, pady=(0, 10))

        tk.Label(form, text="Status", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.combo_status_add = ttk.Combobox(form, values=STATUSES, state="readonly", font=self.fonts['normal'])
        self.combo_status_add.set(STATUSES[0])
        self.combo_status_add.pack(fill=tk.X, pady=(0, 10))
        
        # Image upload button
        btn_add_image = ttk.Button(form, text="📷 Add Image", command=self._on_add_image, 
                                  style='TButton', width=20)
        btn_add_image.pack(fill=tk.X, pady=(0, 10))

        btn_add = ttk.Button(form, text="➕ Add Shirt", command=self._on_add, 
                            style='Success.TButton', width=20)
        btn_add.pack(fill=tk.X)

        # Selection actions
        actions_container = tk.Frame(right, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=1)
        actions_container.pack(fill=tk.X, pady=(0, 15))
        actions_container.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        
        tk.Label(actions_container, text="✏️ Edit Selected Shirt", font=self.fonts['heading'],
                bg=self.colors['bg_panel'], fg=self.colors['text']).pack(anchor=tk.W, padx=15, pady=(12, 8))
        
        actions = tk.Frame(actions_container, bg=self.colors['bg_panel'])
        actions.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Edit fields (pre-filled when shirt is selected)
        tk.Label(actions, text="Name", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_edit_name = ttk.Entry(actions, font=self.fonts['normal'])
        self.entry_edit_name.pack(fill=tk.X, pady=(0, 10))

        tk.Label(actions, text="Color", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_edit_color = ttk.Entry(actions, font=self.fonts['normal'])
        self.entry_edit_color.pack(fill=tk.X, pady=(0, 10))

        tk.Label(actions, text="Size", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.entry_edit_size = ttk.Entry(actions, font=self.fonts['normal'])
        self.entry_edit_size.pack(fill=tk.X, pady=(0, 10))

        tk.Label(actions, text="Status", font=self.fonts['small'], bg=self.colors['bg_panel'],
                fg=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 4))
        self.combo_status_update = ttk.Combobox(actions, values=STATUSES, state="readonly", font=self.fonts['normal'])
        self.combo_status_update.set(STATUSES[0])
        self.combo_status_update.pack(fill=tk.X, pady=(0, 10))
        
        btn_update_image = ttk.Button(actions, text="📷 Change Image", command=self._on_update_image,
                                     style='TButton', width=20)
        btn_update_image.pack(fill=tk.X, pady=(0, 8))
        
        btn_remove_image = ttk.Button(actions, text="🗑️ Remove Image", command=self._on_remove_image,
                                     style='TButton', width=20)
        btn_remove_image.pack(fill=tk.X, pady=(0, 8))

        btn_update = ttk.Button(actions, text="💾 Save Changes", command=self._on_edit_shirt,
                               style='Primary.TButton', width=20)
        btn_update.pack(fill=tk.X, pady=(0, 8))

        btn_delete = ttk.Button(actions, text="🗑️ Delete Shirt", command=self._on_delete,
                               style='Danger.TButton', width=20)
        btn_delete.pack(fill=tk.X)
        
        self.pending_image_path = None

        # Create floating chatbot button (initially hidden overlay will be created on demand)
        self.chatbot_overlay_visible = False
        self._create_floating_chatbot_button()
        self._create_chatbot_overlay()

    # ----- Helpers -----
    def _refresh_all(self) -> None:
        self._refresh_lists()
        self._refresh_counts()
        self._update_image_display()
        self.stats_cache_valid = False  # Invalidate stats cache

    def _on_search_debounced(self) -> None:
        """Debounced search to avoid excessive filtering."""
        if self.search_debounce_id:
            self.after_cancel(self.search_debounce_id)
        self.search_debounce_id = self.after(300, self._on_search)  # 300ms delay
    
    def _refresh_lists(self) -> None:
        # Clear
        for lb in self.listboxes.values():
            lb.delete(0, tk.END)

        # Apply search filter
        display_shirts = self.shirts
        if self.search_filter:
            display_shirts = search_shirts(self.shirts, self.search_filter)

        # Repopulate per status
        for status in STATUSES:
            items = [s for s in display_shirts if s.status == status]
            lb = self.listboxes[status]
            for s in items:
                img_indicator = "📷" if s.image_path else ""
                text = f"#{s.id}: {s.name} | {s.color} | {s.size} {img_indicator}"
                lb.insert(tk.END, text)

    def _refresh_counts(self) -> None:
        counts = counts_by_status(self.shirts)
        total = len(self.shirts)
        for status in STATUSES:
            self.count_labels[status].configure(text=f"{status}: {counts.get(status, 0)}")
        self.total_label.configure(text=f"Total: {total}")

    def _get_current_status_tab(self) -> str:
        idx = self.notebook.index(self.notebook.select())
        return STATUSES[idx]

    def _get_selected_shirt(self) -> Shirt | None:
        status = self._get_current_status_tab()
        lb = self.listboxes[status]
        sel = lb.curselection()
        if not sel:
            return None
        # Extract the ID from the display text (format: #ID: ...)
        text = lb.get(sel[0])
        try:
            hash_idx = text.find('#')
            colon_idx = text.find(':', hash_idx + 1)
            shirt_id = int(text[hash_idx + 1:colon_idx])
        except Exception:
            return None
        for s in self.shirts:
            if s.id == shirt_id:
                return s
        return None
    
    def _update_image_display(self) -> None:
        """Update the image display area with current shirt's image (with caching)."""
        shirt = self.current_shirt
        self.current_image_photo = None
        
        if not shirt:
            self.image_label.configure(image="", text="No shirt selected\n\nSelect a shirt from the list", 
                                       font=self.fonts['normal'], fg=self.colors['text_light'])
            return
        
        image_path = get_image_display_path(shirt.image_path)
        if not image_path or not os.path.exists(image_path):
            self.image_label.configure(image="", text="No image available\n\nClick 'Change Image' to add one",
                                      font=self.fonts['normal'], fg=self.colors['text_light'])
            return
        
        # Check cache first
        cache_key = f"{shirt.id}_{image_path}"
        if cache_key in self.thumbnail_cache:
            cached_photo = self.thumbnail_cache[cache_key]
            self.current_image_photo = cached_photo
            self.image_label.configure(image=cached_photo, text="", bg=self.colors['bg_entry'])
            return
        
        try:
            # Load and resize image
            img = Image.open(image_path)
            img.thumbnail((240, 240), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.current_image_photo = photo  # Keep reference
            # Cache it
            self.thumbnail_cache[cache_key] = photo
            self.image_label.configure(image=photo, text="", bg=self.colors['bg_entry'])
        except Exception as e:
            self.image_label.configure(image="", text=f"Error loading image:\n{str(e)}",
                                      font=self.fonts['small'], fg=self.colors['danger'])

    def _on_shirt_select(self) -> None:
        """Handle shirt selection from listbox."""
        shirt = self._get_selected_shirt()
        self.current_shirt = shirt
        if shirt:
            # Populate edit fields
            self.entry_edit_name.delete(0, tk.END)
            self.entry_edit_name.insert(0, shirt.name)
            self.entry_edit_color.delete(0, tk.END)
            self.entry_edit_color.insert(0, shirt.color)
            self.entry_edit_size.delete(0, tk.END)
            self.entry_edit_size.insert(0, shirt.size)
            self.combo_status_update.set(shirt.status)
            self._update_image_display()
        else:
            self.entry_edit_name.delete(0, tk.END)
            self.entry_edit_color.delete(0, tk.END)
            self.entry_edit_size.delete(0, tk.END)
            self.combo_status_update.set(STATUSES[0])
            self.current_image_photo = None
            self.image_label.configure(image="", text="No shirt selected\n\nSelect a shirt from the list",
                                      font=self.fonts['normal'], fg=self.colors['text_light'])
    
    def _on_window_resize(self, event=None) -> None:
        """Handle window resize events for responsive layout."""
        if event and event.widget == self:
            self.current_width = event.width
            self.current_height = event.height
            self._update_layout()
            # Update overlay position if visible
            if self.chatbot_overlay_visible:
                self.chatbot_overlay.place(relx=0, rely=0.5, relwidth=1.0, relheight=0.5, anchor='sw')
    
    def _determine_layout_mode(self) -> str:
        """Determine layout mode based on window width."""
        if self.current_width < 1000:
            return "small"
        elif self.current_width > 1400:
            return "large"
        else:
            return "medium"
    
    def _switch_to_vertical_layout(self) -> None:
        """Switch to vertical layout for small screens."""
        if hasattr(self, 'content') and hasattr(self, 'left_panel') and hasattr(self, 'right_container'):
            # Check if layout is already vertical
            try:
                pack_info = self.right_container.pack_info()
                if pack_info.get('side') == tk.BOTTOM:
                    return  # Already vertical
            except:
                pass
            
            # Switch to vertical
            self.left_panel.pack_forget()
            self.right_container.pack_forget()
            
            self.left_panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
            self.right_container.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 15), side=tk.BOTTOM)
    
    def _switch_to_horizontal_layout(self) -> None:
        """Switch to horizontal layout for medium/large screens."""
        if hasattr(self, 'content') and hasattr(self, 'left_panel') and hasattr(self, 'right_container'):
            try:
                pack_info = self.right_container.pack_info()
                if pack_info.get('side') == tk.RIGHT:
                    return  # Already horizontal
            except:
                pass
            
            # Switch to horizontal
            self.left_panel.pack_forget()
            self.right_container.pack_forget()
            
            self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
            self.right_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
    
    def _update_layout(self) -> None:
        """Update layout based on current window size."""
        # Update layout mode
        new_mode = self._determine_layout_mode()
        layout_changed = new_mode != self.layout_mode
        self.prev_layout_mode = self.layout_mode
        self.layout_mode = new_mode
        
        # Switch layout orientation if mode changed
        if layout_changed:
            if new_mode == "small":
                self._switch_to_vertical_layout()
            else:
                self._switch_to_horizontal_layout()
        
        # Update right panel width dynamically (25-35% of window for medium/large)
        if hasattr(self, 'right_container'):
            if self.layout_mode == "small":
                # For small screens, right panel takes full width but limited height
                new_width = max(280, int(self.current_width * 0.95))
            else:
                new_width = max(300, min(450, int(self.current_width * 0.3)))
            
            # Right panel width is controlled by pack, so we update canvas width
            if hasattr(self, 'right_canvas'):
                self.right_canvas.configure(width=new_width)
        
        # Update listbox heights dynamically
        if hasattr(self, 'listboxes'):
            if self.layout_mode == "small":
                # Smaller listboxes for small screens
                visible_lines = max(8, min(20, int((self.current_height - 300) / 25)))
            elif self.layout_mode == "large":
                # Larger listboxes for large screens
                visible_lines = max(15, min(35, int((self.current_height - 200) / 25)))
            else:
                visible_lines = max(10, min(30, int((self.current_height - 200) / 25)))
            
            for lb in self.listboxes.values():
                lb.configure(height=visible_lines)
        
        # Chat log height is now in overlay, so it doesn't need dynamic sizing
        # But we can still update it if needed for overlay
        if hasattr(self, 'chat_log') and self.chatbot_overlay_visible:
            # Chat log in overlay uses fixed height, but we can adjust if needed
            pass
        
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
            if hasattr(self, 'total_label'):
                self.total_label.configure(font=fonts['heading'])
        
        # Update entry and listbox fonts
        if hasattr(self, 'search_entry'):
            self.search_entry.configure(font=fonts['normal'])
        if hasattr(self, 'entry_name'):
            self.entry_name.configure(font=fonts['normal'])
            self.entry_color.configure(font=fonts['normal'])
            self.entry_size.configure(font=fonts['normal'])
        if hasattr(self, 'entry_edit_name'):
            self.entry_edit_name.configure(font=fonts['normal'])
            self.entry_edit_color.configure(font=fonts['normal'])
            self.entry_edit_size.configure(font=fonts['normal'])
        if hasattr(self, 'combo_status_add'):
            self.combo_status_add.configure(font=fonts['normal'])
        if hasattr(self, 'combo_status_update'):
            self.combo_status_update.configure(font=fonts['normal'])
        if hasattr(self, 'chat_input'):
            self.chat_input.configure(font=fonts['normal'])
        if hasattr(self, 'chat_log'):
            self.chat_log.configure(font=fonts['small'])
        if hasattr(self, 'listboxes'):
            for lb in self.listboxes.values():
                lb.configure(font=fonts['normal'])
        
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
    
    def _on_add_image(self) -> None:
        """Handle image upload for new shirt."""
        file_path = filedialog.askopenfilename(
            title="Select Shirt Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            self.pending_image_path = file_path
    
    def _on_update_image(self) -> None:
        """Handle image update for selected shirt."""
        shirt = self._get_selected_shirt()
        if not shirt:
            messagebox.showinfo("No Selection", "Please select a shirt to update its image.")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Shirt Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Delete old image
                if shirt.image_path:
                    delete_image(shirt.image_path)
                    # Clear cache
                    cache_key = f"{shirt.id}_{get_image_display_path(shirt.image_path)}"
                    if cache_key in self.thumbnail_cache:
                        del self.thumbnail_cache[cache_key]
                
                # Save new image
                new_path = save_image_from_path(file_path, shirt.id, os.path.basename(file_path))
                mgr_update_shirt(self.shirts, shirt.id, image_path=new_path)
                save_shirts(self.shirts)
                self.current_shirt = shirt  # Refresh
                self._refresh_all()
                messagebox.showinfo("Success", "Image updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update image: {str(e)}")
    
    def _on_remove_image(self) -> None:
        """Remove image from selected shirt."""
        shirt = self._get_selected_shirt()
        if not shirt:
            messagebox.showinfo("No Selection", "Please select a shirt.")
            return
        
        if not shirt.image_path:
            messagebox.showinfo("No Image", "This shirt has no image.")
            return
        
        resp = messagebox.askyesno("Confirm", "Remove image from this shirt?")
        if resp:
            try:
                delete_image(shirt.image_path)
                # Clear cache
                cache_key = f"{shirt.id}_{get_image_display_path(shirt.image_path)}"
                if cache_key in self.thumbnail_cache:
                    del self.thumbnail_cache[cache_key]
                mgr_update_shirt(self.shirts, shirt.id, image_path="")
                save_shirts(self.shirts)
                self.current_shirt = shirt  # Refresh
                self._refresh_all()
                messagebox.showinfo("Success", "Image removed successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove image: {str(e)}")
    
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
    def _on_add(self) -> None:
        name = self.entry_name.get().strip()
        color = self.entry_color.get().strip()
        size = self.entry_size.get().strip()
        status = self.combo_status_add.get().strip()

        if not name or not color or not size:
            messagebox.showwarning("Missing Data", "Name, Color, and Size are required.")
            return
        if status not in STATUSES:
            messagebox.showwarning("Invalid Status", "Please select a valid status.")
            return

        try:
            shirt = mgr_add_shirt(self.shirts, name, color, size, status)
            
            # Handle image upload if provided
            if self.pending_image_path:
                try:
                    image_path = save_image_from_path(self.pending_image_path, shirt.id, os.path.basename(self.pending_image_path))
                    mgr_update_shirt(self.shirts, shirt.id, image_path=image_path)
                except Exception as e:
                    messagebox.showwarning("Image Upload", f"Shirt added but image upload failed: {str(e)}")
                self.pending_image_path = None
            
            save_shirts(self.shirts)
            messagebox.showinfo("Success", f"Shirt #{shirt.id} added successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._refresh_all()

        # Clear inputs
        self.entry_name.delete(0, tk.END)
        self.entry_color.delete(0, tk.END)
        self.entry_size.delete(0, tk.END)
        self.combo_status_add.set(STATUSES[0])

    def _on_edit_shirt(self) -> None:
        """Handle editing shirt details."""
        shirt = self._get_selected_shirt()
        if not shirt:
            messagebox.showinfo("No Selection", "Please select a shirt to edit.")
            return
        
        name = self.entry_edit_name.get().strip()
        color = self.entry_edit_color.get().strip()
        size = self.entry_edit_size.get().strip()
        status = self.combo_status_update.get().strip()
        
        if not name or not color or not size:
            messagebox.showwarning("Missing Data", "Name, Color, and Size are required.")
            return
        if status not in STATUSES:
            messagebox.showwarning("Invalid Status", "Please select a valid status.")
            return
        
        try:
            mgr_update_shirt(self.shirts, shirt.id, name=name, color=color, size=size, status=status)
            save_shirts(self.shirts)
            self.current_shirt = shirt  # Refresh
            # Clear image cache for this shirt
            if shirt.image_path:
                cache_key = f"{shirt.id}_{get_image_display_path(shirt.image_path)}"
                if cache_key in self.thumbnail_cache:
                    del self.thumbnail_cache[cache_key]
            self._refresh_all()
            messagebox.showinfo("Success", "Shirt updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

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
                # Clear cache
                cache_key = f"{shirt.id}_{get_image_display_path(shirt.image_path)}"
                if cache_key in self.thumbnail_cache:
                    del self.thumbnail_cache[cache_key]
            
            mgr_delete_shirt(self.shirts, shirt.id)
            save_shirts(self.shirts)
            self.current_shirt = None
            self._refresh_all()
            messagebox.showinfo("Success", "Shirt deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----- Chatbot Handlers -----
    def _append_chat(self, text: str) -> None:
        if not text:
            return
        # Temporarily enable to insert text, then disable again
        self.chat_log.configure(state=tk.NORMAL)
        self.chat_log.insert(tk.END, text + "\n")
        self.chat_log.see(tk.END)
        self.chat_log.configure(state=tk.DISABLED)

    def _on_chat_send(self) -> None:
        msg = self.chat_input.get().strip()
        if not msg:
            return
        
        self._append_chat(f"You: {msg}")
        
        try:
            # Get response from chatbot (now returns string instead of printing)
            response = chatbot_process(msg, self.shirts)
            
            # Display response in chat log
            if response:
                # Split long responses into multiple lines for better display
                for line in response.splitlines():
                    if line.strip():  # Skip empty lines
                        self._append_chat(f"Bot: {line}")
            
            # Save data and refresh if changes were made
            save_shirts(self.shirts)
            self._refresh_all()
        except Exception as e:
            self._append_chat(f"Bot: ❌ Error processing message: {str(e)}")
        
        self.chat_input.delete(0, tk.END)


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
    app = ShirtInventoryGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
