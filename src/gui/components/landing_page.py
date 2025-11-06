"""Landing page/splash screen component."""
import tkinter as tk
import os
from typing import Optional, Callable
from PIL import Image, ImageTk


class LandingPage(tk.Tk):
    """Splash screen/landing page that displays before main app."""
    
    def __init__(self, on_complete: Callable, colors: dict, duration_ms: int = 2000) -> None:
        """Initialize landing page.
        
        Args:
            on_complete: Callback to execute after duration
            colors: Color scheme dictionary
            duration_ms: How long to show landing page in milliseconds
        """
        super().__init__()
        self.on_complete = on_complete
        self.duration_ms = duration_ms
        self.animation_job = None  # Track animation callback
        self.close_job = None  # Track close callback
        
        # Configure window
        self.title("Shirt Inventory Tracker")
        self.configure(bg=colors.get('bg_main', '#F5F5F5'))
        
        # Remove window decorations for clean splash screen
        self.overrideredirect(True)
        
        # Set window size
        width = 500
        height = 400
        self.geometry(f"{width}x{height}")
        
        # Center on screen
        self._center_window(width, height)
        
        # Build UI
        self._build_ui(colors)
        
        # Schedule auto-close and callback
        self.close_job = self.after(duration_ms, self._close_and_launch)
    
    def _center_window(self, width: int, height: int) -> None:
        """Center window on screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _build_ui(self, colors: dict) -> None:
        """Build landing page UI."""
        # Main container
        container = tk.Frame(self, bg=colors.get('bg_main', '#F5F5F5'))
        container.pack(fill=tk.BOTH, expand=True)
        
        # Logo/image section
        logo_frame = tk.Frame(container, bg=colors.get('bg_main', '#F5F5F5'))
        logo_frame.pack(pady=(60, 30))
        
        logo_path = self._get_logo_path()
        if logo_path and os.path.exists(logo_path):
            try:
                # Load larger logo for landing page (120x120px)
                img = Image.open(logo_path)
                img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(logo_frame, image=logo_photo,
                                     bg=colors.get('bg_main', '#F5F5F5'))
                logo_label.image = logo_photo  # Keep reference
                logo_label.pack()
            except Exception:
                # Fallback to emoji
                logo_label = tk.Label(logo_frame, text="👕", 
                                     font=('Segoe UI', 72),
                                     bg=colors.get('bg_main', '#F5F5F5'),
                                     fg=colors.get('accent', '#8C00FF'))
                logo_label.pack()
        else:
            # Fallback to emoji
            logo_label = tk.Label(logo_frame, text="👕", 
                                 font=('Segoe UI', 72),
                                 bg=colors.get('bg_main', '#F5F5F5'),
                                 fg=colors.get('accent', '#8C00FF'))
            logo_label.pack()
        
        # App name
        title_label = tk.Label(container, 
                               text="Shirt Inventory Tracker",
                               font=('Segoe UI', 28, 'bold'),
                               bg=colors.get('bg_main', '#F5F5F5'),
                               fg=colors.get('text', '#333333'))
        title_label.pack(pady=(0, 10))
        
        # Tagline
        tagline_label = tk.Label(container,
                                text="Organize. Track. Manage.",
                                font=('Segoe UI', 12),
                                bg=colors.get('bg_main', '#F5F5F5'),
                                fg=colors.get('text_light', '#666666'))
        tagline_label.pack(pady=(0, 40))
        
        # Loading indicator
        loading_label = tk.Label(container,
                                text="Loading...",
                                font=('Segoe UI', 10),
                                bg=colors.get('bg_main', '#F5F5F5'),
                                fg=colors.get('text_light', '#666666'))
        loading_label.pack()
        
        # Animate loading dots
        self._animate_loading(loading_label, 0)
    
    def _animate_loading(self, label: tk.Label, dot_count: int) -> None:
        """Animate loading dots."""
        # Check if window still exists (not destroyed)
        try:
            if not self.winfo_exists():
                return
            dots = "." * (dot_count % 4)
            label.configure(text=f"Loading{dots}")
            # Schedule next animation, but only if window still exists
            self.animation_job = self.after(300, lambda: self._animate_loading(label, dot_count + 1))
        except tk.TclError:
            # Window was destroyed, stop animation
            return
    
    def _get_logo_path(self) -> Optional[str]:
        """Get path to logo image file if it exists."""
        try:
            current_file = os.path.abspath(__file__)
        except NameError:
            current_file = os.path.abspath(os.path.join(os.getcwd(), "landing_page.py"))
        
        # Navigate to data directory
        current_dir = os.path.dirname(current_file)
        # Go up from components -> gui -> src -> project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        data_dir = os.path.join(project_root, "data")
        
        # Check for logo files
        logo_names = ["logo.png", "logo.jpg", "logo.jpeg", "logo.gif", "wardrobe.png", "wardrobe.jpg"]
        
        for logo_name in logo_names:
            logo_path = os.path.join(data_dir, logo_name)
            if os.path.exists(logo_path) and os.path.isfile(logo_path):
                return logo_path
        
        return None
    
    def _close_and_launch(self) -> None:
        """Close landing page and launch main app."""
        # Cancel any pending animation callbacks
        if self.animation_job:
            try:
                self.after_cancel(self.animation_job)
            except:
                pass
        
        # Cancel close callback if it exists
        if self.close_job:
            try:
                self.after_cancel(self.close_job)
            except:
                pass
        
        # Destroy window
        try:
            self.destroy()
        except:
            pass
        
        # Launch main app
        if self.on_complete:
            self.on_complete()

