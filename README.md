# Belgian TOB Tax Calculator - Flask Web App

A professional web application for calculating Belgian Tax on Stock Exchange Transactions (TOB) from broker statements.

## 🚀 Features

- **Multi-Broker Support**: Interactive Brokers & Saxo Bank
- **Automatic Detection**: Identifies broker format automatically
- **ECB Exchange Rates**: Uses official ECB rates for currency conversion
- **Smart Grouping**: Automatically groups same-side transactions
- **Multiple Outputs**: Excel, CSV (Belgian format), and Markdown
- **Drag & Drop**: Modern file upload interface
- **Secure**: Files deleted immediately after processing

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package manager)

## 🔧 Installation

### 1. Clone or Download

Download this project folder to your computer.

### 2. Create Virtual Environment (Recommended)

```bash
# Navigate to project folder
cd tob_calculator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Running the Application

### Local Development

```bash
# Make sure you're in the project folder and virtual environment is activated
python app.py
```

The application will start on `http://localhost:5000`

Open your browser and navigate to:
- **Main page**: http://localhost:5000
- **About page**: http://localhost:5000/about

## 📖 How to Use

1. **Upload PDFs**: Drag and drop (or click to browse) your broker PDF statements
2. **Process**: Click "Calculate TOB Tax"
3. **Download**: Get your Excel, CSV, and Markdown reports
4. **Review**: Check the results and download files for your records

## 🗂️ Project Structure

```
tob_calculator/
├── app.py                  # Main Flask application
├── tob_calculator.py       # Core calculation logic
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates
│   ├── base.html          # Base template with styling
│   ├── index.html         # Upload page
│   ├── results.html       # Results display
│   └── about.html         # About/methodology page
├── uploads/               # Temporary upload folder
└── outputs/               # Generated reports folder
```

## 🌐 Deployment Options

### Option 1: Render.com (Free Tier)

1. Create account on [render.com](https://render.com)
2. Create new "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Add to requirements.txt**: `gunicorn==21.2.0`

### Option 2: Railway.app (Free Tier)

1. Create account on [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Railway auto-detects Flask
4. Add environment variable: `PORT=5000`

### Option 3: Fly.io (Free Tier)

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Deploy: `fly launch`
4. Follow prompts

### Option 4: PythonAnywhere (Free Tier)

1. Create account on [pythonanywhere.com](https://pythonanywhere.com)
2. Upload files via Files tab
3. Create new Web app
4. Configure WSGI file to point to your app
5. Reload web app

## 🔐 Production Considerations

Before deploying to production, update these settings in `app.py`:

```python
# Change secret key
app.config['SECRET_KEY'] = 'your-random-secret-key-here'

# Disable debug mode
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

Generate a secure secret key:
```python
import secrets
print(secrets.token_hex(32))
```

## 📊 Supported Brokers

### Interactive Brokers
- Language: English
- Format: Extracts from "Trades" → "Stocks" section
- Currency: Converts using ECB rates
- Grouping: Automatic for same-side transactions

### Saxo Bank
- Language: Dutch/Flemish
- Format: Extracts from "Transacties" section
- Currency: Already in EUR (no conversion needed)
- Grouping: Automatic for same-side transactions

## 🧮 TOB Calculation Rules

- **Rate**: 0.35% (0.0035)
- **Maximum**: €1,600 per transaction
- **Applies to**: Both buy AND sell transactions
- **Day trades**: Both sides taxed separately
- **Grouping**: Multiple same-side trades = 1 transaction

## ⚠️ Known Limitations

1. **PDF Extraction**: Hardcoded for current broker formats
   - May break if brokers change their statement layouts
   - Requires manual updates for new broker formats

2. **Transaction Types**: Currently supports standard stock trades only
   - Does not handle: options, futures, bonds, etc.

3. **Weekend/Holiday Rates**: Uses previous business day if ECB rate unavailable

## 🐛 Troubleshooting

### "No PDF library available"
```bash
pip install pdfplumber
```

### "Failed to fetch ECB rates"
- Check internet connection
- ECB website may be temporarily down
- Try again in a few minutes

### PDF extraction returns no transactions
- Verify your PDF is from a supported broker
- Check that PDF is not password protected
- Ensure PDF contains actual transaction data (not just summary)

## 🛠️ Extending the Application

### Add New Broker Support

1. Add detection logic in `tob_calculator.py`:
```python
def detect_broker(text):
    if 'Your Broker Name' in text:
        return 'Your Broker'
```

2. Add extraction function:
```python
def extract_yourbroker_transactions(text):
    # Parse your broker's format
    pass
```

3. Update `process_statements()` to call your extractor

### Add Claude API Fallback

Replace hardcoded extraction with Claude API call when parsing fails:

```python
import anthropic

def extract_with_claude_api(pdf_path):
    client = anthropic.Anthropic(api_key="your-api-key")
    
    # Read PDF and convert to text/base64
    # Send to Claude with instructions
    # Return structured transaction data
    pass
```

## 📝 License

This project is for educational purposes. Use at your own risk.

## ⚠️ Disclaimer

This tool is for informational purposes only. Always verify calculations with a qualified tax professional. The developer is not responsible for any tax filing errors.

## 🤝 Contributing

This is a learning project! Feel free to:
- Add support for more brokers
- Improve PDF extraction
- Add unit tests
- Enhance the UI
- Add export formats

## 📧 Support

For issues or questions:
1. Check the About page in the application
2. Review this README
3. Test with sample data first

---

**Built with Flask** | **ECB Exchange Rates** | **Made for Belgian Tax Compliance**
