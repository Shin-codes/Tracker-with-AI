"""Messenger-style floating chatbot window component."""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable

from src.chatbot import process_message as chatbot_process
from src.storage import save_shirts


class ChatbotWindow:
    """Messenger-style floating chat window."""
    
    def __init__(self, parent, shirts: list, colors: Dict[str, str], refresh_callback: Callable = None) -> None:
        """Initialize chatbot window.
        
        Args:
            parent: Parent Tk window
            shirts: List of shirt objects
            colors: Color scheme dictionary
            refresh_callback: Optional callback to refresh main window
        """
        self.parent = parent
        self.shirts = shirts
        self.colors = colors
        self.refresh_callback = refresh_callback
        self.chatbot_window_visible = False
        
        self._create_floating_button()
        self._create_chatbot_window()
    
    def _create_floating_button(self) -> None:
        """Create floating chatbot button at bottom right."""
        self.floating_button_frame = tk.Frame(self.parent, bg='', highlightthickness=0)
        self.floating_button_frame.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)
        
        self.floating_button = tk.Button(
            self.floating_button_frame,
            text="💬",
            font=('Segoe UI', 24),
            bg=self.colors['accent'],
            fg='white',
            activebackground=self.colors['accent_hover'],
            activeforeground='white',
            relief=tk.FLAT,
            borderwidth=0,
            cursor='hand2',
            width=3,
            height=1,
            command=self._toggle_chatbot_window
        )
        self.floating_button.pack()
        
        def on_enter(e):
            self.floating_button.configure(bg=self.colors['accent_hover'])
        
        def on_leave(e):
            if not self.chatbot_window_visible:
                self.floating_button.configure(bg=self.colors['accent'])
        
        self.floating_button.bind("<Enter>", on_enter)
        self.floating_button.bind("<Leave>", on_leave)
    
    def _create_chatbot_window(self) -> None:
        """Create Messenger-style floating chat window."""
        self.chatbot_window = tk.Frame(self.parent, bg=self.colors['bg_panel'], relief=tk.FLAT, bd=0)
        self.chatbot_window.configure(highlightbackground=self.colors['border'], highlightthickness=1)
        self.chatbot_window.configure(width=380, height=500)
        
        # Header
        header = tk.Frame(self.chatbot_window, bg=self.colors['accent'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.colors['accent'])
        title_frame.pack(side=tk.LEFT, padx=15, pady=12)
        
        title_icon = tk.Label(title_frame, text="💬", font=('Segoe UI', 16),
                              bg=self.colors['accent'], fg='white')
        title_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        title_label = tk.Label(title_frame, text="Chat Assistant", 
                              font=('Segoe UI', 13, 'bold'), bg=self.colors['accent'], 
                              fg='white')
        title_label.pack(side=tk.LEFT)
        
        close_btn = tk.Button(header, text="✕", font=('Segoe UI', 14),
                             bg=self.colors['accent'], fg='white',
                             activebackground=self.colors['accent_hover'], 
                             activeforeground='white',
                             relief=tk.FLAT, borderwidth=0, cursor='hand2',
                             width=2, height=1, command=self._close_chatbot_window)
        close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        minimize_btn = tk.Button(header, text="−", font=('Segoe UI', 16),
                                bg=self.colors['accent'], fg='white',
                                activebackground=self.colors['accent_hover'], 
                                activeforeground='white',
                                relief=tk.FLAT, borderwidth=0, cursor='hand2',
                                width=2, height=1, command=self._minimize_chatbot_window)
        minimize_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=10)
        
        # Messages container
        messages_container = tk.Frame(self.chatbot_window, bg='#F0F2F5')
        messages_container.pack(fill=tk.BOTH, expand=True)
        
        messages_canvas = tk.Canvas(messages_container, bg='#F0F2F5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(messages_container, orient=tk.VERTICAL, 
                                 command=messages_canvas.yview)
        scrollable_frame = tk.Frame(messages_canvas, bg='#F0F2F5')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: messages_canvas.configure(scrollregion=messages_canvas.bbox("all"))
        )
        
        messages_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        messages_canvas.configure(yscrollcommand=scrollbar.set)
        
        messages_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def on_mousewheel(event):
            messages_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        messages_canvas.bind("<Enter>", lambda e: messages_canvas.bind_all("<MouseWheel>", on_mousewheel))
        messages_canvas.bind("<Leave>", lambda e: messages_canvas.unbind_all("<MouseWheel>"))
        
        self.messages_frame = scrollable_frame
        self.messages_canvas = messages_canvas
        
        # Welcome message
        self._add_bot_message("Hello! I'm your Shirt Inventory Assistant. How can I help you today?")
        
        # Input area
        input_container = tk.Frame(self.chatbot_window, bg=self.colors['bg_panel'], height=60)
        input_container.pack(fill=tk.X, side=tk.BOTTOM)
        input_container.pack_propagate(False)
        
        input_inner = tk.Frame(input_container, bg=self.colors['bg_entry'])
        input_inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self.chat_input = tk.Entry(input_inner, 
                                   font=('Segoe UI', 11),
                                   bg='white',
                                   fg=self.colors['text'],
                                   relief=tk.FLAT,
                                   bd=0,
                                   highlightthickness=1,
                                   highlightbackground=self.colors['border'],
                                   highlightcolor=self.colors['accent'],
                                   insertbackground=self.colors['text'],
                                   borderwidth=0)
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=8)
        
        send_btn = tk.Button(input_inner, text="Send", 
                            font=('Segoe UI', 10, 'bold'),
                            bg=self.colors['accent'],
                            fg='white',
                            activebackground=self.colors['accent_hover'],
                            activeforeground='white',
                            relief=tk.FLAT,
                            borderwidth=0,
                            cursor='hand2',
                            command=self._on_chat_send,
                            padx=15, pady=5)
        send_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=8)
        
        self.chat_input.bind("<Return>", lambda e: self._on_chat_send())
        
        self.chatbot_window.place_forget()
    
    def _add_user_message(self, text: str) -> None:
        """Add user message bubble (right-aligned)."""
        message_frame = tk.Frame(self.messages_frame, bg='#F0F2F5')
        message_frame.pack(fill=tk.X, padx=10, pady=4)
        
        bubble = tk.Frame(message_frame, bg=self.colors['accent'])
        bubble.pack(side=tk.RIGHT, padx=(50, 10))
        
        label = tk.Label(bubble, text=text, 
                        font=('Segoe UI', 10),
                        bg=self.colors['accent'],
                        fg='white',
                        wraplength=200,
                        justify=tk.LEFT,
                        padx=12, pady=8)
        label.pack()
        
        self.messages_canvas.update_idletasks()
        self.messages_canvas.configure(scrollregion=self.messages_canvas.bbox("all"))
        self.messages_canvas.yview_moveto(1.0)
    
    def _add_bot_message(self, text: str) -> None:
        """Add bot message bubble (left-aligned)."""
        message_frame = tk.Frame(self.messages_frame, bg='#F0F2F5')
        message_frame.pack(fill=tk.X, padx=10, pady=4)
        
        bubble = tk.Frame(message_frame, bg='white')
        bubble.pack(side=tk.LEFT, padx=(10, 50))
        
        label = tk.Label(bubble, text=text, 
                        font=('Segoe UI', 10),
                        bg='white',
                        fg=self.colors['text'],
                        wraplength=200,
                        justify=tk.LEFT,
                        padx=12, pady=8)
        label.pack()
        
        self.messages_canvas.update_idletasks()
        self.messages_canvas.configure(scrollregion=self.messages_canvas.bbox("all"))
        self.messages_canvas.yview_moveto(1.0)
    
    def _toggle_chatbot_window(self) -> None:
        """Toggle window visibility."""
        if self.chatbot_window_visible:
            self._close_chatbot_window()
        else:
            self._show_chatbot_window()
    
    def _show_chatbot_window(self) -> None:
        """Show chatbot window."""
        self.chatbot_window_visible = True
        self.chatbot_window.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-80)
        self.chatbot_window.lift()
        self.floating_button_frame.lift()
        self.floating_button.configure(bg=self.colors['accent_hover'])
    
    def _close_chatbot_window(self) -> None:
        """Close chatbot window."""
        self.chatbot_window_visible = False
        self.chatbot_window.place_forget()
        self.floating_button.configure(bg=self.colors['accent'])
    
    def _minimize_chatbot_window(self) -> None:
        """Minimize chatbot window."""
        self._close_chatbot_window()
    
    def _on_chat_send(self) -> None:
        """Handle chat send."""
        message = self.chat_input.get().strip()
        if not message:
            return
        
        self._add_user_message(message)
        self.chat_input.delete(0, tk.END)
        self.chat_input.focus()
        
        try:
            response = chatbot_process(message, self.shirts)
            self._add_bot_message(response)
            
            if any(keyword in message.lower() for keyword in ['add', 'delete', 'remove']):
                if self.refresh_callback:
                    self.refresh_callback()
                save_shirts(self.shirts)
        except Exception as e:
            self._add_bot_message(f"I encountered an error: {str(e)}")
    
    def update_position(self) -> None:
        """Update window position on resize."""
        if self.chatbot_window_visible:
            self.chatbot_window.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-80)

