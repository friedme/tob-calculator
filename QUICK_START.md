# Quick Start Guide

## For Complete Beginners

### Step 1: Install Python
1. Go to https://python.org
2. Download Python 3.11 or newer
3. Run installer (check "Add Python to PATH")

### Step 2: Open Terminal/Command Prompt
- **Windows**: Search for "cmd" or "PowerShell"
- **Mac**: Search for "Terminal"
- **Linux**: Open your terminal

### Step 3: Navigate to Project Folder
```bash
cd path/to/tob_calculator
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

If that fails, try:
```bash
python -m pip install -r requirements.txt
```

### Step 5: Run the App
```bash
python app.py
```

### Step 6: Open in Browser
Go to: http://localhost:5000

## Common Issues

### "python is not recognized"
- Reinstall Python and check "Add to PATH"
- Or use full path: `C:\Python311\python.exe app.py`

### "pip is not recognized"
- Use: `python -m pip install -r requirements.txt`

### "Permission denied"
- Run terminal as administrator (Windows)
- Use `sudo` on Mac/Linux

### Port already in use
Change port in app.py:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

## Need Help?

1. Read the full README.md
2. Check the About page in the app
3. Google the error message

## Video Tutorial (Concept)

If you were making a tutorial, you'd show:
1. Download Python
2. Download project folder
3. Open terminal
4. Run commands above
5. Upload PDF
6. Download results

---

**You're ready to go!** 🚀
