# Installation Guide

## Windows Installation (Recommended)

### Step 1: Install Python

1. Download Python 3.8+ from: https://www.python.org/downloads/
2. Run installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"

### Step 2: Extract Files

1. Extract `tob_calculator.zip` to a location like:
   - `C:\TOB_Calculator`
   - `C:\Users\YourName\Documents\TOB_Calculator`

### Step 3: First Run

1. Open the `tob_calculator` folder
2. Double-click `START_TOB_CALCULATOR.bat`
3. Wait for dependency installation (1-2 minutes first time)
4. Browser will open automatically at `http://localhost:5000`

### Step 4: Usage

1. Drag and drop your broker PDF files
2. Click "Bereken TOB"
3. Download your results

---

## Alternative: Command Line Installation

```bash
# Navigate to folder
cd C:\path\to\tob_calculator

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Then open browser to: http://localhost:5000

---

## macOS/Linux Installation

```bash
# Navigate to folder
cd /path/to/tob_calculator

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Then open browser to: http://localhost:5000

---

## Verifying Installation

After starting, you should see:

```
============================================================
Belgian TOB Tax Calculator
============================================================
PDF Library: pdfplumber
PDF Generation: Available
Upload folder: C:\...\tob_calculator\uploads
Output folder: C:\...\tob_calculator\outputs
============================================================
Starting server at http://localhost:5000
Press Ctrl+C to stop
============================================================
```

---

## Troubleshooting Installation

### "Python is not recognized"
- Python is not installed or not in PATH
- Reinstall Python with "Add to PATH" checked

### "pip is not recognized"
- Run: `python -m pip install -r requirements.txt`

### "Permission denied"
- Run Command Prompt as Administrator

### "Port 5000 already in use"
- Edit `app.py` line 545, change `port=5000` to `port=5001`

### Dependencies fail to install
- Try: `python -m pip install --upgrade pip`
- Then: `pip install -r requirements.txt`

---

## Manual Dependency Installation

If `requirements.txt` fails, install one by one:

```bash
pip install Flask==3.0.0
pip install openpyxl==3.1.2
pip install pdfplumber==0.11.0
pip install reportlab==4.0.7
pip install requests==2.31.0
```

---

## Uninstallation

1. Stop the calculator (Ctrl+C or STOP_TOB_CALCULATOR.bat)
2. Delete the `tob_calculator` folder
3. Done - no registry changes or system modifications

---

## Updating Python Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate.bat

# Update all dependencies
pip install --upgrade -r requirements.txt
```

---

**Need help?** Provide Claude with your error message and system details.
