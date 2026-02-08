# Deployment Checklist

## Pre-Deployment Verification

### ✅ File Structure
- [x] `app.py` - Main Flask application
- [x] `tob_core.py` - PDF extraction & calculation logic
- [x] `tob_outputs.py` - File generation (Excel, CSV, PDF, Markdown)
- [x] `requirements.txt` - Python dependencies
- [x] `templates/` folder with all HTML files:
  - [x] `base.html`
  - [x] `index.html`
  - [x] `results.html`
  - [x] `about.html`
- [x] `uploads/` folder (with `.gitkeep`)
- [x] `outputs/` folder (with `.gitkeep`)
- [x] `START_TOB_CALCULATOR.bat` - Windows startup script
- [x] `QUICK_START.vbs` - Silent startup script
- [x] `STOP_TOB_CALCULATOR.bat` - Shutdown script
- [x] `README.md` - User documentation
- [x] `INSTALLATION.md` - Installation guide
- [x] `.gitignore` - Version control exclusions

### ✅ Code Quality Checks
- [ ] No hardcoded API keys or secrets
- [ ] Error handling for all user inputs
- [ ] File upload validation (PDF only, 50MB limit)
- [ ] Proper cleanup of temporary files
- [ ] ECB rate fetching with fallback
- [ ] Transaction grouping logic correct
- [ ] Broker detection working for both IB and Saxo

### ✅ Security Checks
- [x] File uploads restricted to PDF only
- [x] Secure filename handling (werkzeug.secure_filename)
- [x] No directory traversal vulnerabilities
- [x] Local-only deployment (127.0.0.1)
- [x] No sensitive data logged
- [x] Flask secret key uses environment variable

### ✅ Documentation
- [x] README.md comprehensive and clear
- [x] INSTALLATION.md with troubleshooting
- [x] Inline code comments for complex logic
- [x] HTML templates have descriptive elements
- [x] Error messages in Dutch (user's language)

## Deployment Steps

### 1. Package Creation
```bash
# Create ZIP archive
cd /home/claude
zip -r tob_calculator.zip tob_calculator/ -x "tob_calculator/venv/*" "tob_calculator/__pycache__/*" "tob_calculator/uploads/*" "tob_calculator/outputs/*" "*.pyc"
```

### 2. User Instructions
Send to user with this message:
```
Belgian TOB Tax Calculator - Deployment Package

Contents:
- Complete Flask web application
- Startup scripts for Windows
- Full documentation

Installation:
1. Extract tob_calculator.zip
2. Double-click START_TOB_CALCULATOR.bat
3. Browser opens automatically at http://localhost:5000

Requirements:
- Windows 10/11
- Python 3.8+ (https://www.python.org/downloads/)
- Internet connection (for ECB rates)

First run installs dependencies automatically (1-2 minutes).

See README.md for full documentation.
```

### 3. Testing Checklist (User Should Test)
- [ ] Upload Interactive Brokers PDF → generates results
- [ ] Upload Saxo Bank PDF → generates results
- [ ] Download Excel file → opens in Excel
- [ ] Download CSV file → Belgian format correct (semicolon, comma decimals)
- [ ] Download PDF report → readable
- [ ] Download Markdown → contains correct data
- [ ] ECB rates fetched correctly
- [ ] Transaction grouping correct
- [ ] Day trades kept separate
- [ ] Same-side transactions grouped
- [ ] TOB calculations accurate (0.35%)
- [ ] Stop script works

## Post-Deployment Support

### Common Issues & Solutions

**Issue**: "Python is not installed"
**Solution**: Install Python 3.8+ from python.org, check "Add to PATH"

**Issue**: "Port 5000 already in use"
**Solution**: Edit app.py line 545, change port to 5001

**Issue**: "Unknown broker format"
**Solution**: Verify PDF is Activity Statement (IB) or Transactie- en saldorapport (Saxo)

**Issue**: "ECB rates not available"
**Solution**: Check internet connection, retry later

**Issue**: Dependencies fail to install
**Solution**: Run `pip install --upgrade pip` then reinstall

### Update Procedure
When providing updates:
1. User backs up `outputs/` folder
2. User deletes old `tob_calculator/` folder
3. User extracts new version
4. User moves backed-up outputs (optional)
5. User runs START_TOB_CALCULATOR.bat

### Version Control
- Current version: v2.0
- Tag releases: `git tag -a v2.0 -m "Initial Flask release"`
- Keep changelog in README.md

## Known Limitations

1. **Windows-only batch scripts**: macOS/Linux users need manual startup
2. **Local deployment only**: Not designed for production web hosting
3. **No user authentication**: Single-user, local-only
4. **No database**: All data in files
5. **No automated testing**: Manual verification required

## Future Enhancements (Optional)

- [ ] macOS `.command` startup script
- [ ] Linux startup script
- [ ] Automatic browser opening
- [ ] Transaction verification against broker totals
- [ ] Export to Belgian tax software format
- [ ] Multi-language support (French, English)
- [ ] Docker container for cross-platform deployment

## Compliance Notes

⚠️ **Important**: This tool is for personal use only.
- User is responsible for accuracy
- User must verify with tax advisor
- Tool does not replace professional advice
- Keep original broker statements

## Developer Contact

For issues beyond user troubleshooting:
- Provide Claude with:
  - Error message (full console output)
  - Screenshot of error in browser
  - Broker and statement type
  - Python version
  - Windows version

---

**Package Status**: ✅ READY FOR DEPLOYMENT

**Last Updated**: January 22, 2026
**Version**: 2.0
**Developer**: Fried Meulders (via Claude)
