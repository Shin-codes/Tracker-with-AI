import tkinter as tk
from tkinter import ttk, messagebox

# Reuse data model and persistence from the CLI module
from shirt_inventory_tracker import (
    load_data,
    save_data,
    generate_next_id,
    STATUSES,
)


class ShirtInventoryGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Shirt Inventory Tracker - GUI")
        self.geometry("820x520")

        # In-memory data
        self.shirts = load_data()

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

        # Right-side: Actions + Form
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
            items = [s for s in self.shirts if s.get("status") == status]
            lb = self.listboxes[status]
            for s in items:
                text = f"#{s['id']}: {s['name']} | {s['color']} | {s['size']}"
                lb.insert(tk.END, text)

    def _refresh_counts(self) -> None:
        counts = {status: 0 for status in STATUSES}
        for s in self.shirts:
            st = s.get("status")
            if st in counts:
                counts[st] += 1
        total = len(self.shirts)
        for status in STATUSES:
            self.count_labels[status].configure(text=f"{status}: {counts[status]}")
        self.total_label.configure(text=f"Total: {total}")

    def _get_current_status_tab(self) -> str:
        idx = self.notebook.index(self.notebook.select())
        return STATUSES[idx]

    def _get_selected_shirt(self) -> dict | None:
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
            if s.get("id") == shirt_id:
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

        new_shirt = {
            "id": generate_next_id(self.shirts),
            "name": name,
            "color": color,
            "size": size,
            "status": status,
        }
        self.shirts.append(new_shirt)
        save_data(self.shirts)
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
        if new_status == shirt.get("status"):
            messagebox.showinfo("No Change", "The shirt already has that status.")
            return
        shirt["status"] = new_status
        save_data(self.shirts)
        self._refresh_all()

    def _on_delete(self) -> None:
        shirt = self._get_selected_shirt()
        if not shirt:
            return
        resp = messagebox.askyesno(
            "Confirm Delete",
            f"Delete #{shirt['id']} - {shirt['name']}?",
            icon="warning",
        )
        if not resp:
            return
        try:
            self.shirts.remove(shirt)
            save_data(self.shirts)
            self._refresh_all()
        except ValueError:
            messagebox.showerror("Error", "Could not delete the selected shirt.")


def main() -> None:
    app = ShirtInventoryGUI()
    app.mainloop()


if __name__ == "__main__":
    main()


