Shirt Inventory Tracker
=======================

A beginner-friendly, modular Python application to track shirts across three states: In Drawer, Laundry, and Worn. Includes a CLI and can be extended to GUI/chatbot later.

Project Structure
-----------------

```
shirt_inventory_tracker/
├── data/
│   └── shirts.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── storage.py
│   ├── inventory_manager.py
│   └── cli.py
├── tests/
│   ├── __init__.py
│   └── test_inventory.py
├── requirements.txt
└── README.md
```

Usage
-----

Run the CLI or Chatbot:

```
python -m src.main
# choose 1 for CLI or 2 for Chatbot
```

Data is stored in `data/shirts.json`. The app auto-loads on start and saves after changes.

Features
--------
- Add a shirt with name, color, size, and status
- View shirts grouped by status
- Update status of any shirt
- Delete a shirt
- Counts per status and total
- Robust input validation and error handling

Chatbot examples
----------------
- add blue large shirt to laundry
- move blue large shirt to drawer
- show inventory
- count shirts
- delete blue large shirt

Testing
-------
```
python -m unittest discover -s tests -p "test_*.py"
```

Notes
-----
- Uses only Python standard library
- JSON file is human-readable

