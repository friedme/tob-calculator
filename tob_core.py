"""
TOB Core Module - PDF Extraction and Processing
Handles extraction of stock transactions from Belgian broker statements
Supports: Interactive Brokers (English) and Saxo Bank (Dutch/Flemish)
"""

import re
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

# Try importing PDF libraries
try:
    import pdfplumber
    PDF_LIBRARY = 'pdfplumber'
except ImportError:
    try:
        from pypdf import PdfReader
        PDF_LIBRARY = 'pypdf'
    except ImportError:
        PDF_LIBRARY = None


class Broker(Enum):
    INTERACTIVE_BROKERS = "Interactive Brokers"
    SAXO_BANK = "Saxo Bank"
    UNKNOWN = "Unknown"


class ExtractionError(Exception):
    """Custom exception for extraction errors with detailed messages"""
    def __init__(self, message: str, error_type: str = "extraction_error", details: dict = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}


@dataclass
class Transaction:
    """Represents a single stock transaction"""
    date: str              # YYYY-MM-DD
    broker: str
    stock: str
    trans_type: str        # 'Buy' or 'Sell'
    shares: int
    currency: str
    amount: float
    original_line: str = ""  # For debugging


@dataclass
class ExtractionResult:
    """Result of PDF extraction"""
    transactions: List[Transaction]
    broker: Broker
    warnings: List[str]
    raw_text: str
    success: bool
    error_message: str = ""


# =============================================================================
# PDF TEXT EXTRACTION
# =============================================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using available library
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        ExtractionError: If no PDF library is available or extraction fails
    """
    if PDF_LIBRARY is None:
        raise ExtractionError(
            "No PDF library available. Install pdfplumber: pip install pdfplumber",
            "library_missing"
        )
    
    try:
        if PDF_LIBRARY == 'pdfplumber':
            return _extract_with_pdfplumber(pdf_path)
        else:
            return _extract_with_pypdf(pdf_path)
    except Exception as e:
        raise ExtractionError(
            f"Failed to read PDF: {str(e)}",
            "pdf_read_error",
            {"path": pdf_path, "original_error": str(e)}
        )


def _extract_with_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (preserves layout better)"""
    import pdfplumber
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_with_pypdf(pdf_path: str) -> str:
    """Extract text using pypdf"""
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


# =============================================================================
# BROKER DETECTION
# =============================================================================

def detect_broker(text: str) -> Broker:
    """
    Detect broker type from PDF text content
    
    Args:
        text: Extracted PDF text
        
    Returns:
        Broker enum value
    """
    text_lower = text.lower()
    
    # Interactive Brokers markers
    ib_markers = [
        'interactive brokers',
        'activity statement',
        'trades',
        'realized & unrealized',
        'mark-to-market'
    ]
    
    # Saxo Bank markers (Dutch/Flemish)
    saxo_markers = [
        'saxo bank',
        'transacties',
        'transactie- en saldorapport',
        'zelf beleggen',
        'boekingsbedrag'
    ]
    
    ib_score = sum(1 for marker in ib_markers if marker in text_lower)
    saxo_score = sum(1 for marker in saxo_markers if marker in text_lower)
    
    if ib_score >= 2:
        return Broker.INTERACTIVE_BROKERS
    elif saxo_score >= 2:
        return Broker.SAXO_BANK
    else:
        return Broker.UNKNOWN


# =============================================================================
# INTERACTIVE BROKERS EXTRACTION
# =============================================================================
def extract_ib_transactions(text: str) -> ExtractionResult:
    """
    Extract transactions from Interactive Brokers statement
    
    Format (date on separate line):
    Line 1: 2025-11-26,
    Line 2: MCE -350,000 0.2150 0.2300 75,250.00 -61.44 ...
    Line 3: 18:00:07
    
    CRITICAL: 
    - JPY stocks have INTEGER proceeds (no decimals)
    - Other currencies have DECIMAL proceeds
    - Symbols can be mixed case (e.g., ZEGl)
    """
    transactions = []
    warnings = []
    
    lines = text.split('\n')
    
    current_currency = None
    in_trades_section = False
    current_date = None
    
    # Pattern to detect Trades section start
    trades_section_pattern = re.compile(r'^Trades\s*$', re.IGNORECASE)
    
    # Pattern for date line: 2025-11-26,
    date_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}),')
    
    # Pattern for JPY stocks - proceeds are INTEGERS (no decimal point)
    # Japanese stocks always end in .T
    jpy_transaction_pattern = re.compile(
        r'^(\d+\.T)\s+'                  # Symbol (JPY stocks end in .T)
        r'(-?[\d,]+)\s+'                 # Quantity
        r'[\d,.]+\s+'                    # T.Price
        r'(?:[\d,.]+\s+)?'               # Optional C.Price
        r'(-?[\d,]+)\s+'                 # Proceeds (INTEGER - no decimal!)
        r'(-?[\d,.]+)'                   # Comm/Fee (has decimal)
    )
    
    # Pattern for non-JPY stocks - proceeds HAVE decimals
    # FIXED: Allow mixed case symbols (e.g., ZEGl)
    regular_transaction_pattern = re.compile(
        r'^([A-Za-z0-9.]+)\s+'           # Symbol - MIXED CASE!
        r'(-?[\d,]+)\s+'                 # Quantity
        r'[\d,.]+\s+'                    # T.Price
        r'(?:[\d,.]+|--)\s+'             # C.Price
        r'(-?[\d,]+\.\d+)\s+'            # Proceeds (HAS decimal point!)
        r'(-?[\d,.]+)'                   # Comm/Fee
    )
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for Trades section start
        if trades_section_pattern.match(line):
            in_trades_section = True
            continue
        
        if not in_trades_section:
            continue
        
        # Check for currency headers
        for curr in ['AUD', 'CAD', 'GBP', 'JPY', 'USD', 'EUR', 'SEK', 'CHF', 'HKD', 'NOK', 'DKK']:
            if line == curr or line == f'Stocks{curr}':
                current_currency = curr
                break
        
        # Check for date line
        date_match = date_pattern.match(line)
        if date_match:
            current_date = date_match.group(1)
            continue
        
        # Check for section end markers
        if any(marker in line.lower() for marker in ['forex', 'equity and index options']):
            break
        
        # Skip Total lines
        if line.startswith('Total'):
            continue
        
        # Try JPY pattern first (for Japanese stocks)
        jpy_match = jpy_transaction_pattern.match(line)
        if jpy_match and current_date:
            symbol, quantity_str, proceeds_str, comm_str = jpy_match.groups()
            
            try:
                quantity = int(quantity_str.replace(',', ''))
                proceeds = abs(float(proceeds_str.replace(',', '')))
            except ValueError:
                continue
            
            trans_type = 'Sell' if quantity < 0 else 'Buy'
            
            transactions.append(Transaction(
                date=current_date,
                broker=Broker.INTERACTIVE_BROKERS.value,
                stock=symbol,
                trans_type=trans_type,
                shares=abs(quantity),
                currency='JPY',  # Japanese stocks are always JPY
                amount=proceeds,
                original_line=line
            ))
            continue
        
        # Try regular pattern for non-JPY stocks
        regular_match = regular_transaction_pattern.match(line)
        if regular_match and current_date:
            symbol, quantity_str, proceeds_str, comm_str = regular_match.groups()
            
            # Skip Total lines
            if 'Total' in symbol:
                continue
            
            try:
                quantity = int(quantity_str.replace(',', ''))
                proceeds = abs(float(proceeds_str.replace(',', '')))
            except ValueError:
                continue
            
            trans_type = 'Sell' if quantity < 0 else 'Buy'
            
            # Determine currency
            trade_currency = current_currency
            if not trade_currency:
                # Look back for currency context
                context = ' '.join(lines[max(0, i-10):i])
                for curr in ['AUD', 'CAD', 'GBP', 'USD', 'EUR', 'SEK']:
                    if curr in context:
                        trade_currency = curr
                        break
            
            if not trade_currency:
                warnings.append(f"Could not determine currency for {symbol} on {current_date}, defaulting to USD")
                trade_currency = 'USD'
            
            transactions.append(Transaction(
                date=current_date,
                broker=Broker.INTERACTIVE_BROKERS.value,
                stock=symbol,
                trans_type=trans_type,
                shares=abs(quantity),
                currency=trade_currency,
                amount=proceeds,
                original_line=line
            ))
    
    # Alternative extraction if pattern-based didn't work well
    if not transactions:
        transactions, alt_warnings = _extract_ib_alternative(text)
        warnings.extend(alt_warnings)
    
    if not transactions:
        return ExtractionResult(
            transactions=[],
            broker=Broker.INTERACTIVE_BROKERS,
            warnings=warnings,
            raw_text=text,
            success=False,
            error_message="No transactions found in Interactive Brokers statement."
        )
    
    return ExtractionResult(
        transactions=transactions,
        broker=Broker.INTERACTIVE_BROKERS,
        warnings=warnings,
        raw_text=text,
        success=True
    )

def _extract_ib_alternative(text: str) -> Tuple[List[Transaction], List[str]]:
    """
    Alternative extraction method for IB statements
    Uses more flexible pattern matching for different PDF layouts
    """
    transactions = []
    warnings = []
    
    # Look for the Trades table specifically
    # Pattern for trades with date, symbol, and numbers
    # More flexible pattern that captures the key elements
    
    flexible_pattern = re.compile(
        r'([A-Z0-9.]+(?:\.[A-Z]+)?)\s+'   # Symbol
        r'(\d{4}-\d{2}-\d{2})'             # Date
        r'[,\s]+[\d:]+\s+'                 # Time separator
        r'(-?[\d,]+)\s+'                   # Quantity
        r'[\d.]+\s+'                       # Price
        r'[\d.]+\s+'                       # Another price or --
        r'(-?[\d,]+\.?\d*)'                # Amount (proceeds)
    )
    
    # Detect currency sections
    current_currency = 'USD'  # Default
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Update currency context
        for curr in ['AUD', 'CAD', 'GBP', 'JPY', 'USD', 'EUR', 'SEK']:
            if f'Stocks{curr}' in line or line == curr:
                current_currency = curr
                break
        
        # Japanese stocks
        if re.search(r'\d+\.T', line):
            current_currency = 'JPY'
        
        match = flexible_pattern.search(line)
        if match:
            symbol, date, quantity_str, amount_str = match.groups()
            
            # Skip headers and non-trade lines
            if symbol.upper() in ['SYMBOL', 'TOTAL', 'SUBTOTAL']:
                continue
            
            quantity = int(quantity_str.replace(',', ''))
            amount = abs(float(amount_str.replace(',', '')))
            
            trans_type = 'Sell' if quantity < 0 else 'Buy'
            
            # Override currency for Japanese stocks
            trade_currency = current_currency
            if re.match(r'^\d+\.T$', symbol):
                trade_currency = 'JPY'
            
            transactions.append(Transaction(
                date=date,
                broker=Broker.INTERACTIVE_BROKERS.value,
                stock=symbol,
                trans_type=trans_type,
                shares=abs(quantity),
                currency=trade_currency,
                amount=amount,
                original_line=line
            ))
    
    return transactions, warnings


# =============================================================================
# SAXO BANK EXTRACTION
# =============================================================================

def extract_saxo_transactions(text: str) -> ExtractionResult:
    """
    Extract transactions from Saxo Bank statement (Dutch/Flemish format)
    
    Saxo Format (from Transacties section):
    - Two accounts: EUR (98900/1008313EUR) and USD (98900/1517751USD)
    - Columns: Transactiedatum, Valutadatum, TransactieID, Product, Instrument, 
               Instrumentvaluta, Type, Openen/sluiten, Aantal, Koers, 
               Omrekeningskoers, Gerealiseerde W/V, Boekingsbedrag, Booked Costs
    - CRITICAL: Boekingsbedrag is in the ACCOUNT currency (EUR or USD), not instrument currency
    - EUR account amounts are in EUR, USD account amounts are in USD
    - Verkoop = Sell, Koop = Buy
    - Negative Aantal = Sell
    
    Args:
        text: Extracted PDF text
        
    Returns:
        ExtractionResult with transactions
    """
    transactions = []
    warnings = []
    
    lines = text.split('\n')
    
    # Track current account currency
    current_account_currency = None
    in_transactions_section = False
    
    # Pattern to detect account sections
    # e.g., "Transacties - Zelf Beleggen (98900/1008313EUR), EUR"
    # e.g., "Transacties - Zelf Beleggen (98900/1517751USD), USD"
    account_section_pattern = re.compile(
        r'Transacties.*?(\d+/\d+)(EUR|USD).*?(EUR|USD)',
        re.IGNORECASE
    )
    
    # Pattern for transaction rows
    # Format: dd-mmm-yyyy dd-mmm-yyyy TransID Product Instrument Currency Type Action Aantal Koers Rate P/L Amount Costs
    # Example: 27-nov-2025 01-dec-2025 6494810500 Aandelen JDC Group AG EUR Verkoop SLUITEN -889 26,000 1,0000 -2.806,14 23.102,44 -11,56
    
    # Dutch month abbreviations
    dutch_months = {
        'jan': '01', 'feb': '02', 'mrt': '03', 'apr': '04', 
        'mei': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'okt': '10', 'nov': '11', 'dec': '12'
    }
    
    # Transaction line pattern - flexible to handle various formats
    # Looking for: date, transaction ID (digits), product type, instrument name, currency, type, etc.
    saxo_trans_pattern = re.compile(
        r'(\d{1,2})-([a-z]{3})-(\d{4})\s+'                    # Transaction date (dd-mmm-yyyy)
        r'(\d{1,2})-([a-z]{3})-(\d{4})\s+'                    # Value date
        r'(\d+)\s+'                                            # Transaction ID
        r'(Aandelen|Effecten)\s+'                              # Product type
        r'(.+?)\s+'                                            # Instrument name
        r'(EUR|USD)\s+'                                        # Instrument currency
        r'(Verkoop|Koop)\s+'                                   # Type (Sell/Buy)
        r'(SLUITEN|OPENING)\s+'                                # Open/Close
        r'(-?[\d.]+)\s+'                                       # Aantal (shares) - may have period as thousands separator
        r'([\d,.]+)\s+'                                        # Koers (price)
        r'([\d,.]+)\s+'                                        # Omrekeningskoers (conversion rate)
        r'(-?[\d.,]+|-)\s+'                                    # Gerealiseerde W/V (P/L)
        r'(-?[\d.,]+)\s*'                                      # Boekingsbedrag (Amount)
    , re.IGNORECASE)
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for account section header
        account_match = account_section_pattern.search(line)
        if account_match:
            _, account_type, section_currency = account_match.groups()
            current_account_currency = section_currency
            in_transactions_section = True
            continue
        
        # Alternative: detect from simpler patterns
        if 'Transacties - Zelf Beleggen' in line:
            in_transactions_section = True
            if 'EUR), EUR' in line or '1008313EUR' in line:
                current_account_currency = 'EUR'
            elif 'USD), USD' in line or '1517751USD' in line:
                current_account_currency = 'USD'
            continue
        
        # Skip if not in transactions section
        if not in_transactions_section:
            continue
        
        # Skip non-transaction lines
        if 'Cashbedrag' in line or 'Totaal' in line:
            continue
        
        # Try to match transaction line
        match = saxo_trans_pattern.search(line)
        if match:
            (trans_day, trans_month, trans_year,
             val_day, val_month, val_year,
             trans_id, product, instrument, inst_currency,
             trans_type_nl, open_close,
             aantal, koers, conv_rate, pl, amount) = match.groups()
            
            # Parse date
            month_num = dutch_months.get(trans_month.lower(), '01')
            date = f"{trans_year}-{month_num}-{trans_day.zfill(2)}"
            
            # Parse aantal (shares) - remove period thousands separator
            shares_str = aantal.replace('.', '').replace(',', '.')
            shares = abs(int(float(shares_str)))
            
            # Parse amount (Boekingsbedrag) - Belgian format: 23.102,44 -> 23102.44
            amount_str = amount.replace('.', '').replace(',', '.')
            amount_value = abs(float(amount_str))
            
            # Determine transaction type
            trans_type = 'Sell' if trans_type_nl.lower() == 'verkoop' else 'Buy'
            
            # CRITICAL: Use account currency, not instrument currency
            # The Boekingsbedrag is in the account's currency
            currency = current_account_currency or inst_currency
            
            transactions.append(Transaction(
                date=date,
                broker=Broker.SAXO_BANK.value,
                stock=instrument.strip(),
                trans_type=trans_type,
                shares=shares,
                currency=currency,
                amount=amount_value,
                original_line=line
            ))
    
    # Try alternative extraction if pattern-based didn't work
    if not transactions:
        transactions, alt_warnings = _extract_saxo_alternative(text)
        warnings.extend(alt_warnings)
    
    if not transactions:
        return ExtractionResult(
            transactions=[],
            broker=Broker.SAXO_BANK,
            warnings=warnings,
            raw_text=text,
            success=False,
            error_message="No transactions found in Saxo Bank statement. "
                         "Check that the PDF contains 'Transacties' sections."
        )
    
    return ExtractionResult(
        transactions=transactions,
        broker=Broker.SAXO_BANK,
        warnings=warnings,
        raw_text=text,
        success=True
    )


def _extract_saxo_alternative(text: str) -> Tuple[List[Transaction], List[str]]:
    """
    Alternative extraction for Saxo statements
    Uses line-by-line parsing with more flexible patterns
    """
    transactions = []
    warnings = []
    
    dutch_months = {
        'jan': '01', 'feb': '02', 'mrt': '03', 'apr': '04', 
        'mei': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'okt': '10', 'nov': '11', 'dec': '12'
    }
    
    lines = text.split('\n')
    current_currency = 'EUR'  # Default
    
    for i, line in enumerate(lines):
        # Track account currency
        if '1008313EUR' in line or 'EUR), EUR' in line:
            current_currency = 'EUR'
        elif '1517751USD' in line or 'USD), USD' in line:
            current_currency = 'USD'
        
        # Look for transaction patterns
        # Date pattern: dd-mmm-yyyy
        date_match = re.search(r'(\d{1,2})-([a-z]{3})-(\d{4})', line, re.IGNORECASE)
        if not date_match:
            continue
        
        # Must have Aandelen (stocks) and Verkoop/Koop
        if 'Aandelen' not in line:
            continue
        if 'Verkoop' not in line and 'Koop' not in line:
            continue
        
        # Skip cash transactions
        if 'Cashbedrag' in line:
            continue
        
        # Extract date
        day, month_nl, year = date_match.groups()
        month_num = dutch_months.get(month_nl.lower(), '01')
        date = f"{year}-{month_num}-{day.zfill(2)}"
        
        # Determine type
        trans_type = 'Sell' if 'Verkoop' in line else 'Buy'
        
        # Extract instrument name - appears between Aandelen and (EUR|USD)
        inst_match = re.search(r'Aandelen\s+(.+?)\s+(EUR|USD)', line)
        if inst_match:
            instrument = inst_match.group(1).strip()
        else:
            instrument = "Unknown"
        
        # Extract amount - look for Belgian format number patterns
        # The Boekingsbedrag is typically the largest positive number
        amounts = re.findall(r'(?<![\d-])(\d{1,3}(?:\.\d{3})*,\d{2})(?!\d)', line)
        if amounts:
            # Parse all amounts and take the appropriate one
            parsed_amounts = []
            for amt in amounts:
                amt_float = float(amt.replace('.', '').replace(',', '.'))
                parsed_amounts.append(amt_float)
            
            # The Boekingsbedrag is usually positive and one of the larger values
            positive_amounts = [a for a in parsed_amounts if a > 0]
            if positive_amounts:
                amount_value = max(positive_amounts)
            else:
                amount_value = max(parsed_amounts) if parsed_amounts else 0
        else:
            continue  # Can't find amount
        
        # Extract shares - look for negative number for sells
        shares_match = re.search(r'(-?\d{1,3}(?:\.\d{3})*)\s+[\d,]+\s+[\d,]+', line)
        if shares_match:
            shares_str = shares_match.group(1).replace('.', '')
            shares = abs(int(shares_str))
        else:
            shares = 0
        
        if amount_value > 0 and shares > 0:
            transactions.append(Transaction(
                date=date,
                broker=Broker.SAXO_BANK.value,
                stock=instrument,
                trans_type=trans_type,
                shares=shares,
                currency=current_currency,
                amount=amount_value,
                original_line=line
            ))
    
    return transactions, warnings


# =============================================================================
# ECB RATE FETCHING
# =============================================================================

def fetch_ecb_rates(dates_needed: set) -> Dict[str, Dict[str, float]]:
    """
    Fetch ECB exchange rates from XML feed
    
    Args:
        dates_needed: Set of date strings in 'YYYY-MM-DD' format
    
    Returns:
        dict: {date: {currency: rate}}
        
    Raises:
        ExtractionError: If rates cannot be fetched
    """
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        xml_content = response.content
    except requests.exceptions.Timeout:
        raise ExtractionError(
            "ECB rate server timeout. Please try again.",
            "ecb_timeout"
        )
    except requests.exceptions.ConnectionError:
        raise ExtractionError(
            "Cannot connect to ECB rate server. Check internet connection.",
            "ecb_connection_error"
        )
    except Exception as e:
        raise ExtractionError(
            f"Failed to fetch ECB rates: {str(e)}",
            "ecb_fetch_error",
            {"original_error": str(e)}
        )
    
    return parse_ecb_xml(xml_content, dates_needed)


def parse_ecb_xml(xml_content: bytes, dates_needed: set) -> Dict[str, Dict[str, float]]:
    """Parse ECB XML and extract rates for needed dates"""
    ns = {
        'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
        'default': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'
    }
    
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ExtractionError(
            f"Invalid ECB XML format: {str(e)}",
            "ecb_parse_error"
        )
    
    rates = {}
    all_available_dates = []
    
    # First pass: collect all available dates and their rates
    for date_cube in root.findall('.//default:Cube[@time]', ns):
        date = date_cube.get('time')
        all_available_dates.append(date)
        
        if date in dates_needed:
            rates[date] = {'EUR': 1.0}  # EUR to EUR is always 1.0
            for curr_cube in date_cube.findall('default:Cube[@currency]', ns):
                currency = curr_cube.get('currency')
                rate = float(curr_cube.get('rate'))
                rates[date][currency] = rate
    
    # Handle missing dates (weekends/holidays) - use previous business day
    for date in dates_needed:
        if date not in rates:
            rates[date] = _get_rate_with_fallback(root, date, ns, all_available_dates)
    
    return rates


def _get_rate_with_fallback(root, date: str, ns: dict, available_dates: list) -> Dict[str, float]:
    """Get rate for date, falling back to previous business day if needed"""
    current_date = datetime.strptime(date, '%Y-%m-%d')
    
    # Try up to 7 days back (to handle long holiday periods)
    for i in range(1, 8):
        prev_date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
        
        for date_cube in root.findall('.//default:Cube[@time]', ns):
            if date_cube.get('time') == prev_date:
                rates = {'EUR': 1.0}
                for curr_cube in date_cube.findall('default:Cube[@currency]', ns):
                    currency = curr_cube.get('currency')
                    rate = float(curr_cube.get('rate'))
                    rates[currency] = rate
                return rates
    
    raise ExtractionError(
        f"No ECB rate found for {date} or 7 days prior. "
        "This date may be outside the ECB historical data range.",
        "ecb_rate_missing",
        {"date": date}
    )


# =============================================================================
# TRANSACTION GROUPING
# =============================================================================

def group_transactions(transactions: List[Transaction]) -> List[Dict[str, Any]]:
    """
    Group transactions by date + stock + type
    
    Rules:
    - Same-side transactions (multiple buys OR multiple sells on same day) = GROUP into 1 transaction
    - Opposite-side transactions (day trades with both buy AND sell) = KEEP SEPARATE
    - Belgian law taxes both sides of a day trade separately
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        List of grouped transaction dictionaries
    """
    grouped = defaultdict(lambda: {
        'shares': 0,
        'amount': 0.0,
        'transactions': []
    })
    
    for t in transactions:
        # Group key: date + broker + stock + type + currency
        key = (t.date, t.broker, t.stock, t.trans_type, t.currency)
        grouped[key]['shares'] += t.shares
        grouped[key]['amount'] += t.amount
        grouped[key]['transactions'].append(t)
    
    result = []
    for key, data in grouped.items():
        date, broker, stock, trans_type, currency = key
        result.append({
            'date': date,
            'broker': broker,
            'stock': stock,
            'type': trans_type,
            'shares': data['shares'],
            'currency': currency,
            'amount': round(data['amount'], 2),
            'grouped_count': len(data['transactions'])
        })
    
    # Sort by date, then broker, then stock
    return sorted(result, key=lambda x: (x['date'], x['broker'], x['stock']))


# =============================================================================
# TOB CALCULATION
# =============================================================================

def calculate_tob(transactions: List[Dict], ecb_rates: Dict[str, Dict[str, float]]) -> List[Dict]:
    """
    Calculate TOB for all transactions
    
    TOB Rate: 0.35% (0.0035)
    Conversion: EUR = Amount / ECB_Rate
    
    Args:
        transactions: List of grouped transaction dicts
        ecb_rates: ECB rate dictionary
        
    Returns:
        List of transactions with calculated TOB
    """
    results = []
    
    for t in transactions:
        date = t['date']
        currency = t['currency']
        amount = t['amount']
        
        # Get ECB rate
        if date not in ecb_rates:
            raise ExtractionError(
                f"No ECB rate data for date {date}",
                "missing_rate",
                {"date": date}
            )
        
        if currency not in ecb_rates[date]:
            raise ExtractionError(
                f"No ECB rate for {currency} on {date}",
                "missing_currency_rate",
                {"currency": currency, "date": date}
            )
        
        rate = ecb_rates[date][currency]
        
        # Convert to EUR
        # ECB rate format: 1 EUR = rate units of foreign currency
        # So: EUR = Foreign / Rate
        # For EUR: rate is 1.0, so eur_amount = amount
        eur_amount = round(amount / rate, 2)
        
        # Calculate TOB at 0.35%
        tob = round(eur_amount * 0.0035, 2)
        
        # Apply maximum cap (EUR 1,600 per transaction)
        tob = min(tob, 1600.00)
        
        results.append({
            **t,
            'rate': rate,
            'eur_amount': eur_amount,
            'tob': tob
        })
    
    return results


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_statements(pdf_paths: List[str]) -> Dict[str, Any]:
    """
    Main processing function
    
    Args:
        pdf_paths: List of paths to PDF files
        
    Returns:
        Dictionary with:
        - transactions: List of processed transactions with TOB
        - total_eur: Total EUR amount
        - total_tob: Total TOB tax
        - ecb_rates: ECB rates used
        - warnings: Any warnings generated
        - brokers: List of brokers found
        
    Raises:
        ExtractionError: If processing fails
    """
    all_transactions = []
    all_warnings = []
    brokers_found = set()
    
    if not pdf_paths:
        raise ExtractionError(
            "No PDF files provided",
            "no_files"
        )
    
    # Extract transactions from all PDFs
    for pdf_path in pdf_paths:
        try:
            text = extract_text_from_pdf(pdf_path)
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(
                f"Failed to read PDF file: {pdf_path}",
                "pdf_read_error",
                {"path": pdf_path, "error": str(e)}
            )
        
        broker = detect_broker(text)
        brokers_found.add(broker.value)
        
        if broker == Broker.INTERACTIVE_BROKERS:
            result = extract_ib_transactions(text)
        elif broker == Broker.SAXO_BANK:
            result = extract_saxo_transactions(text)
        else:
            raise ExtractionError(
                f"Unknown broker format in {pdf_path}. "
                "Supported brokers: Interactive Brokers, Saxo Bank",
                "unknown_broker",
                {"path": pdf_path}
            )
        
        if not result.success:
            raise ExtractionError(
                result.error_message,
                "extraction_failed",
                {"path": pdf_path, "broker": broker.value}
            )
        
        all_transactions.extend(result.transactions)
        all_warnings.extend(result.warnings)
    
    if not all_transactions:
        raise ExtractionError(
            "No transactions found in any of the uploaded PDFs. "
            "Please verify the PDFs contain stock transactions.",
            "no_transactions"
        )
    
    # Group transactions
    grouped = group_transactions(all_transactions)
    
    # Get unique dates for ECB rate fetching
    dates_needed = set(t['date'] for t in grouped)
    
    # Fetch ECB rates
    ecb_rates = fetch_ecb_rates(dates_needed)
    
    # Calculate TOB
    results = calculate_tob(grouped, ecb_rates)
    
    # Calculate totals
    total_eur = sum(r['eur_amount'] for r in results)
    total_tob = sum(r['tob'] for r in results)
    
    return {
        'transactions': results,
        'total_eur': round(total_eur, 2),
        'total_tob': round(total_tob, 2),
        'ecb_rates': ecb_rates,
        'warnings': all_warnings,
        'brokers': list(brokers_found),
        'transaction_count': len(results)
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_belgian_number(num: float, decimals: int = 2) -> str:
    """
    Format number in Belgian style
    Belgian format: 1.234,56 (period for thousands, comma for decimals)
    
    Args:
        num: Number to format
        decimals: Number of decimal places
        
    Returns:
        Belgian-formatted string
    """
    if decimals == 0:
        formatted = f"{int(num):,}".replace(',', '.')
    else:
        int_part = int(num)
        dec_part = round(num - int_part, decimals)
        
        # Format integer with periods
        int_str = f"{int_part:,}".replace(',', '.')
        
        # Format decimal with comma
        dec_str = f"{dec_part:.{decimals}f}"[1:]  # Get ".XX" part
        dec_str = dec_str.replace('.', ',')  # Change to ",XX"
        
        formatted = int_str + dec_str
    
    return formatted


def validate_transaction_data(transactions: List[Dict]) -> List[str]:
    """
    Validate transaction data for common issues
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    for i, t in enumerate(transactions):
        # Check for zero amounts
        if t.get('amount', 0) <= 0:
            warnings.append(f"Transaction {i+1}: Zero or negative amount for {t.get('stock', 'unknown')}")
        
        # Check for zero shares
        if t.get('shares', 0) <= 0:
            warnings.append(f"Transaction {i+1}: Zero or negative shares for {t.get('stock', 'unknown')}")
        
        # Check for valid date
        try:
            datetime.strptime(t.get('date', ''), '%Y-%m-%d')
        except ValueError:
            warnings.append(f"Transaction {i+1}: Invalid date format for {t.get('stock', 'unknown')}")
        
        # Check for known currency
        known_currencies = {'EUR', 'USD', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'SEK', 'NOK', 'DKK', 'HKD'}
        if t.get('currency', '') not in known_currencies:
            warnings.append(f"Transaction {i+1}: Unknown currency {t.get('currency', '')} for {t.get('stock', 'unknown')}")
    
    return warnings
