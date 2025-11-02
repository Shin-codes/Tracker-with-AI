# How to Change the Logo

## Quick Guide

To add your custom logo to the Shirt Inventory Tracker, simply place your logo image file in the `data/` folder with one of these names:

### Supported Logo File Names:
- `logo.png` (recommended)
- `logo.jpg`
- `logo.jpeg`
- `logo.gif`
- `wardrobe.png`
- `wardrobe.jpg`

### Steps:

1. **Prepare your logo image**
   - Format: PNG, JPG, JPEG, or GIF
   - Recommended: PNG with transparent background
   - Size: Any size (will be automatically resized)

2. **Place the file**
   - Copy your logo file
   - Paste it into the `data/` folder in your project
   - Rename it to `logo.png` (or one of the supported names above)

3. **Restart the application**
   - Close the application if it's running
   - Run it again: `python shirt_inventory_gui.py`
   - Your logo will appear automatically!

## Where the Logo Appears

Your logo will be displayed in **two places**:

1. **Main Window Header** (Top Left)
   - Small logo (40x40 pixels)
   - Appears next to the title "Shirt Inventory Tracker"

2. **Splash Screen** (Loading Screen)
   - Larger logo (up to 300x200 pixels)
   - Appears in the center with the title

## Logo Requirements

- **Formats**: PNG, JPG, JPEG, GIF
- **Size**: Any size (auto-resized)
- **Background**: Transparent PNG recommended for best results
- **Location**: Must be in the `data/` folder

## If Logo Doesn't Appear

If you place a logo file but it doesn't show:

1. **Check the file name** - Must be exactly one of the supported names
2. **Check the location** - Must be in the `data/` folder (not `data/images/`)
3. **Check the format** - Must be a valid image file
4. **Restart the app** - Close and reopen the application

If the logo still doesn't appear, the app will automatically fall back to the 👕 emoji icon.

## Example File Structure

```
Shirt Inventory Tracker/
├── data/
│   ├── logo.png          ← Your logo goes here!
│   ├── shirts.json
│   └── images/
│       └── ...
├── src/
└── ...
```

## Tips

- **Best Format**: PNG with transparency
- **Recommended Size**: 
  - For header: Square (e.g., 200x200px)
  - For splash: Landscape or square (e.g., 400x200px or 300x300px)
- **File Size**: Keep it reasonable (< 1MB recommended)

---

**That's it!** Just place your logo file in the `data/` folder with the correct name, and it will automatically appear in the application.

