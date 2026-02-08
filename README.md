# Belgian TOB Tax Calculator

**Automated calculation of Belgian Tax on Stock Exchange Transactions (Taks op Beursverrichtingen)**

Calculate TOB tax from broker statements (Interactive Brokers & Saxo Bank) using exact ECB exchange rates.

---

## 📋 Quick Start

### First Time Setup

1. **Extract the folder** to your computer (e.g., `C:\TOB_Calculator`)

2. **Double-click `START_TOB_CALCULATOR.bat`**
   - First run will install dependencies (takes 1-2 minutes)
   - A browser window will open automatically at `http://localhost:5000`

3. **Upload your broker PDFs** and click "Bereken TOB"

4. **Download results** (Excel, CSV, PDF, Markdown)

### Subsequent Runs

- **Double-click `QUICK_START.vbs`** for silent startup (no console window)
- OR **Double-click `START_TOB_CALCULATOR.bat`** for visible console

### Stopping the Calculator

- Press `Ctrl+C` in the console window
- OR **Double-click `STOP_TOB_CALCULATOR.bat`**

---

## 🗂️ File Structure

```
tob_calculator/
├── START_TOB_CALCULATOR.bat  ← Start the calculator (console visible)
├── QUICK_START.vbs            ← Start silently (no console)
├── STOP_TOB_CALCULATOR.bat    ← Stop the calculator
├── requirements.txt           ← Python dependencies
├── app.py                     ← Main Flask application
├── tob_core.py                ← PDF extraction & TOB calculation
├── tob_outputs.py             ← File generation (Excel, CSV, etc.)
├── templates/                 ← HTML templates
│   ├── base.html
│   ├── index.html
│   ├── results.html
│   └── about.html
├── uploads/                   ← Temporary PDF storage
├── outputs/                   ← Generated files
└── venv/                      ← Python virtual environment (auto-created)
```

---

## 🦅 Supported Brokers

### Interactive Brokers
- **Statement Type**: Activity Statement (English)
- **Format**: PDF
- **Currencies**: USD, GBP, EUR, CAD, AUD, JPY, SEK, CHF, etc.
- **Features**:
  - Automatic commission exclusion
  - Japanese stocks supported (e.g., 3836.T)
  - Multi-currency conversion via ECB rates

### Saxo Bank
- **Statement Type**: Transactie- en saldorapport (Dutch/Flemish)
- **Format**: PDF
- **Accounts**: EUR and USD accounts
- **Features**:
  - Proper handling of account-specific currencies
  - Automatic cash transaction filtering
  - Support for both "Koop" (Buy) and "Verkoop" (Sell)

---

## ⚙️ System Requirements

### Required
- **Windows 10/11** (7/8 should work but untested)
- **Python 3.8+** ([Download here](https://www.python.org/downloads/))
- **Internet connection** (for ECB exchange rate fetching)

### Python Libraries (auto-installed)
- Flask (web framework)
- pdfplumber (PDF reading)
- openpyxl (Excel generation)
- reportlab (PDF generation)
- requests (ECB API access)

---

## 🔧 Advanced Configuration

### Change Port (if 5000 is in use)

Edit `app.py`, line 545:
```python
app.run(debug=True, host='127.0.0.1', port=5000)  # Change 5000 to 5001, 8080, etc.
```

### Folder Locations

By default:
- **Uploads**: `./uploads` (temporary, auto-cleaned)
- **Outputs**: `./outputs` (your results)

To change, edit `app.py`, lines 40-41:
```python
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['OUTPUT_FOLDER'] = Path(__file__).parent / 'outputs'
```

### File Size Limit

Default: 50MB per file

To change, edit `app.py`, line 42:
```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Increase or decrease
```

---

## 📊 Output Files

Each calculation generates **4 files**:

| File | Format | Purpose |
|------|--------|---------|
| `belgian_tob_tax_YYYYMMDD_HHMMSS.xlsx` | Excel | Professional report with formatting |
| `belgian_tob_tax_YYYYMMDD_HHMMSS.csv` | CSV | Belgian format (`;` delimiter, `,` decimal) for import |
| `belgian_tob_tax_YYYYMMDD_HHMMSS.pdf` | PDF | Printable report for tax authority |
| `TOB_Tax_Summary_YYYYMMDD_HHMMSS.md` | Markdown | Text summary with methodology |

### File Contents
- **Transaction details**: Date, stock, type, shares, amount, currency
- **ECB exchange rates**: Exact rates used for each transaction date
- **EUR conversions**: Original amount → EUR amount
- **TOB calculations**: 0.35% tax per transaction
- **Summary statistics**: Total transactions, total EUR amount, total TOB

---

## 🧮 Calculation Methodology

### TOB Rate
- **0.35%** (0.0035) of EUR transaction amount
- **Maximum per transaction**: €1,600
- **Minimum**: No minimum

### Exchange Rates
- **Source**: European Central Bank (ECB) official XML feed
- **Fetched fresh** for every calculation (no caching)
- **Accuracy**: 4 decimal places
- **URL**: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml

### Transaction Grouping
- **Same stock + same day + same type** (all buys OR all sells) = **1 transaction**
- **Same stock + same day + different types** (buys AND sells) = **2+ transactions** (day trades - both sides taxed)
- **Different days** = always separate transactions

### Broker-Specific Handling

**Interactive Brokers:**
- Uses "Proceeds" field (excludes commissions automatically)
- Negative quantity = Sell, Positive = Buy
- Groups same-side transactions

**Saxo Bank:**
- EUR account transactions: amounts already in EUR (no conversion)
- USD account transactions: amounts in USD (requires ECB conversion)
- "Aantal" column = final booking amount in account currency
- Filters out "Storting/opname" (deposits/withdrawals)

---

## ❗ Important Notes

### Tax Compliance
- This tool is a **helper** for TOB calculation
- **Always verify** results with your tax advisor or accountant
- Keep your **original broker statements** for records
- **You are responsible** for the accuracy of your tax filing

### Data Privacy
- All processing happens **locally on your PC**
- **No data** is sent to external servers (except ECB for rates)
- **No tracking** or analytics
- PDFs are **temporarily stored** and can be deleted

### ECB Exchange Rates
- Rates are fetched **fresh every time** (not cached)
- If ECB server is down, calculation will fail
- Weekend/holiday rates use **previous business day**

---

## 🐛 Troubleshooting

### "Python is not installed or not in PATH"
**Solution**: Install Python from https://www.python.org
- During installation, check "Add Python to PATH"

### "ERROR: Failed to create virtual environment"
**Solution**: Run as Administrator or check disk space

### "Onbekend brokerformaat" (Unknown broker format)
**Solution**: 
- Ensure you're uploading the correct statement type
- Interactive Brokers: Activity Statement (English)
- Saxo Bank: Transactie- en saldorapport (Dutch)

### "ECB wisselkoersen niet beschikbaar"
**Solutions**:
- Check internet connection
- Try again later (ECB server may be down)
- Check firewall/antivirus blocking connections

### "Geen transacties gevonden" (No transactions found)
**Possible causes**:
- PDF contains only cash transactions, dividends, or options
- Statement is from a period with no stock trades
- PDF format has changed (contact developer)

### Calculator won't start
1. Check Python is installed: `python --version` in Command Prompt
2. Manually install dependencies: `pip install -r requirements.txt`
3. Check if port 5000 is already in use (change port in `app.py`)

### Port 5000 already in use
**Solution**: Edit `app.py` line 545, change port to 5001 or 8080

---

## 🔄 Updating

When I provide a new version:

1. **Backup your `outputs/` folder** (your old results)
2. **Delete the old `tob_calculator/` folder**
3. **Extract the new version**
4. **Move your backed-up `outputs/`** folder to new location (optional)
5. **Run `START_TOB_CALCULATOR.bat`** to install new dependencies

---

## 🆘 Support

### Self-Help
1. Check this README
2. Check `about.html` in the calculator (Info page)
3. Check console output for error messages

### Contact Developer
**If issues persist**: Provide Claude with:
- Error message (full text from console)
- Screenshot of error in browser
- Which broker and statement type
- Python version (`python --version`)

---

## 📝 Version History

### v2.0 (January 2026)
- Complete Flask web application
- Drag-and-drop interface
- Support for both Interactive Brokers and Saxo Bank
- Multiple output formats (Excel, CSV, PDF, Markdown)
- Comprehensive error handling
- Belgian number formatting
- Automatic ECB rate fetching

### v1.0 (December 2025)
- Initial command-line version
- Interactive Brokers support only
- Basic Excel output

---

## 📜 License

**Personal Use Only**

This tool is provided "as-is" for personal TOB tax calculations. You are responsible for verifying all calculations and compliance with Belgian tax law.

---

## 🙏 Acknowledgments

- **European Central Bank** for providing official exchange rates
- **Interactive Brokers** and **Saxo Bank** for detailed PDF statements
- **Flask** and **Python community** for excellent tools

---

**Made with ❤️ for Belgian investors**
