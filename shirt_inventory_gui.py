import tkinter as tk
from tkinter import ttk, messagebox
import io
from contextlib import redirect_stdout

# Migrate GUI to use modular src package (shared with CLI/Chatbot)
from src.models import Shirt, STATUSES
from src.storage import load_shirts, save_shirts
from src.inventory_manager import (
    add_shirt as mgr_add_shirt,
    update_status as mgr_update_status,
    delete_shirt as mgr_delete_shirt,
    counts_by_status,
)
from src.chatbot import process_message as chatbot_process


class ShirtInventoryGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Shirt Inventory Tracker - GUI")
        self.geometry("820x520")

        # In-memory data (shared with CLI/Chatbot)
        self.shirts = load_shirts()

        # Build UI
        self._build_widgets()
        self._refresh_all()

    # ----- UI Construction -----
    def _build_widgets(self) -> None:
        # Top: Counts
        counts_frame = ttk.Frame(self)
        counts_frame.pack(fill=tk.X, padx=10, pady=(10, 6))
        self.count_labels = {}
        for status in STATUSES:
            lbl = ttk.Label(counts_frame, text=f"{status}: 0")
            lbl.pack(side=tk.LEFT, padx=(0, 16))
            self.count_labels[status] = lbl
        self.total_label = ttk.Label(counts_frame, text="Total: 0")
        self.total_label.pack(side=tk.LEFT)

        # Main content: Notebook (tabs) + Right-side form
        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.notebook = ttk.Notebook(content)
        self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.listboxes = {}
        for status in STATUSES:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=status)

            listbox = tk.Listbox(frame, height=18)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=8, padx=(0, 8))
            listbox.configure(yscrollcommand=scrollbar.set)

            self.listboxes[status] = listbox

        # Right-side: Actions + Form + Chatbot
        right = ttk.Frame(content)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Add form
        form = ttk.LabelFrame(right, text="Add New Shirt")
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Name:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        self.entry_name = ttk.Entry(form)
        self.entry_name.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(form, text="Color:").pack(anchor=tk.W, padx=8, pady=(4, 0))
        self.entry_color = ttk.Entry(form)
        self.entry_color.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(form, text="Size:").pack(anchor=tk.W, padx=8, pady=(4, 0))
        self.entry_size = ttk.Entry(form)
        self.entry_size.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(form, text="Status:").pack(anchor=tk.W, padx=8, pady=(4, 0))
        self.combo_status_add = ttk.Combobox(form, values=STATUSES, state="readonly")
        self.combo_status_add.set(STATUSES[0])
        self.combo_status_add.pack(fill=tk.X, padx=8, pady=(4, 8))

        btn_add = ttk.Button(form, text="Add Shirt", command=self._on_add)
        btn_add.pack(fill=tk.X, padx=8, pady=(0, 8))

        # Selection actions
        actions = ttk.LabelFrame(right, text="Selected Shirt")
        actions.pack(fill=tk.X)

        ttk.Label(actions, text="New Status:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        self.combo_status_update = ttk.Combobox(actions, values=STATUSES, state="readonly")
        self.combo_status_update.set(STATUSES[0])
        self.combo_status_update.pack(fill=tk.X, padx=8, pady=4)

        btn_update = ttk.Button(actions, text="Update Status", command=self._on_update_status)
        btn_update.pack(fill=tk.X, padx=8, pady=(0, 6))

        btn_delete = ttk.Button(actions, text="Delete Shirt", command=self._on_delete)
        btn_delete.pack(fill=tk.X, padx=8, pady=(0, 8))

        # Bottom: Refresh
        btn_refresh = ttk.Button(right, text="Refresh", command=self._refresh_all)
        btn_refresh.pack(fill=tk.X, pady=(10, 0))

        # Chatbot panel
        bot = ttk.LabelFrame(right, text="Chatbot Assistant")
        bot.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Chat log with scrollbar
        log_frame = ttk.Frame(bot)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))
        self.chat_log = tk.Text(log_frame, height=10, state=tk.NORMAL, wrap=tk.WORD)
        self.chat_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.chat_log.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_log.configure(yscrollcommand=log_scroll.set)

        # Input row
        input_frame = ttk.Frame(bot)
        input_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        send_btn = ttk.Button(input_frame, text="Send", command=self._on_chat_send)
        send_btn.pack(side=tk.LEFT, padx=(6, 0))
        # Enter key binding
        self.chat_input.bind("<Return>", lambda e: self._on_chat_send())

    # ----- Helpers -----
    def _refresh_all(self) -> None:
        self._refresh_lists()
        self._refresh_counts()

    def _refresh_lists(self) -> None:
        # Clear
        for lb in self.listboxes.values():
            lb.delete(0, tk.END)

        # Repopulate per status
        for status in STATUSES:
            items = [s for s in self.shirts if s.status == status]
            lb = self.listboxes[status]
            for s in items:
                text = f"#{s.id}: {s.name} | {s.color} | {s.size}"
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
            messagebox.showinfo("No Selection", "Please select a shirt in the list.")
            return None
        # Extract the ID from the display text (format: #ID: ...)
        text = lb.get(sel[0])
        try:
            hash_idx = text.find('#')
            colon_idx = text.find(':', hash_idx + 1)
            shirt_id = int(text[hash_idx + 1:colon_idx])
        except Exception:
            messagebox.showerror("Error", "Could not parse selected item.")
            return None
        for s in self.shirts:
            if s.id == shirt_id:
                return s
        messagebox.showerror("Error", "Selected shirt not found.")
        return None

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
            mgr_add_shirt(self.shirts, name, color, size, status)
            save_shirts(self.shirts)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._refresh_all()

        # Clear inputs
        self.entry_name.delete(0, tk.END)
        self.entry_color.delete(0, tk.END)
        self.entry_size.delete(0, tk.END)
        self.combo_status_add.set(STATUSES[0])

    def _on_update_status(self) -> None:
        shirt = self._get_selected_shirt()
        if not shirt:
            return
        new_status = self.combo_status_update.get().strip()
        if new_status not in STATUSES:
            messagebox.showwarning("Invalid Status", "Please select a valid status.")
            return
        if new_status == shirt.status:
            messagebox.showinfo("No Change", "The shirt already has that status.")
            return
        try:
            mgr_update_status(self.shirts, shirt.id, new_status)
            save_shirts(self.shirts)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._refresh_all()

    def _on_delete(self) -> None:
        shirt = self._get_selected_shirt()
        if not shirt:
            return
        resp = messagebox.askyesno(
            "Confirm Delete",
            f"Delete #{shirt.id} - {shirt.name}?",
            icon="warning",
        )
        if not resp:
            return
        try:
            mgr_delete_shirt(self.shirts, shirt.id)
            save_shirts(self.shirts)
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----- Chatbot Handlers -----
    def _append_chat(self, text: str) -> None:
        if not text:
            return
        self.chat_log.insert(tk.END, text + "\n")
        self.chat_log.see(tk.END)

    def _on_chat_send(self) -> None:
        msg = self.chat_input.get().strip()
        if not msg:
            return
        self._append_chat(f"You: {msg}")
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                chatbot_process(msg, self.shirts)
        finally:
            output = buf.getvalue().strip()
            if output:
                for line in output.splitlines():
                    self._append_chat(f"Bot: {line}")
        save_shirts(self.shirts)
        self._refresh_all()
        self.chat_input.delete(0, tk.END)


def main() -> None:
    app = ShirtInventoryGUI()
    app.mainloop()


if __name__ == "__main__":
    main()


