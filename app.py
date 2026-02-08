"""
Belgian TOB Tax Calculator - Flask Web Application
Calculates Tax on Stock Exchange Transactions (Taks op Beursverrichtingen)
from broker statements (Interactive Brokers, Saxo Bank)

Local deployment - runs on your PC for bi-monthly tax filing
"""

import os
import json
import traceback
from datetime import datetime
from pathlib import Path
import webbrowser
from threading import Timer

from flask import (
    Flask, render_template, request, send_file, 
    flash, redirect, url_for, jsonify
)
from werkzeug.utils import secure_filename

# Import our modules
from tob_core import (
    process_statements, ExtractionError, detect_broker, 
    extract_text_from_pdf, Broker, PDF_LIBRARY
)
from tob_outputs import (
    generate_excel, generate_csv, generate_pdf, 
    generate_markdown, REPORTLAB_AVAILABLE
)


# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

# Get the directory containing this script
BASE_DIR = Path(__file__).parent.absolute()

# Initialize Flask with explicit paths
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / 'templates'),
    static_folder=str(BASE_DIR / 'static')  # For future use
)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tob-calculator-local-dev-key')
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['OUTPUT_FOLDER'] = Path(__file__).parent / 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max (broker PDFs can be large)
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure folders exist
app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(parents=True, exist_ok=True)


# =============================================================================
# ERROR TYPES AND MESSAGES
# =============================================================================

ERROR_MESSAGES = {
    'no_files': {
        'title': 'Geen bestanden geüpload',
        'message': 'Selecteer één of meer PDF-bestanden van uw broker.',
        'suggestion': 'Sleep PDF-bestanden naar het uploadgebied of klik om bestanden te selecteren.'
    },
    'invalid_files': {
        'title': 'Ongeldige bestanden',
        'message': 'Alleen PDF-bestanden worden geaccepteerd.',
        'suggestion': 'Zorg ervoor dat u de originele PDF-statements van uw broker uploadt.'
    },
    'unknown_broker': {
        'title': 'Onbekend brokerformaat',
        'message': 'Het PDF-bestand kon niet worden herkend als een Interactive Brokers of Saxo Bank statement.',
        'suggestion': 'Ondersteunde brokers: Interactive Brokers (Engels) en Saxo Bank (Nederlands). '
                     'Controleer of u het juiste statement uploadt.'
    },
    'no_transactions': {
        'title': 'Geen transacties gevonden',
        'message': 'Er konden geen aandelentransacties worden gevonden in de geüploade PDF.',
        'suggestion': 'Controleer of het PDF-bestand daadwerkelijk aandelentransacties bevat. '
                     'Cash transacties, dividenden, en opties worden niet verwerkt.'
    },
    'pdf_read_error': {
        'title': 'PDF kon niet worden gelezen',
        'message': 'Het PDF-bestand kon niet worden geopend of gelezen.',
        'suggestion': 'Controleer of het bestand niet beschadigd is. Probeer het bestand opnieuw te downloaden van uw broker.'
    },
    'ecb_error': {
        'title': 'ECB wisselkoersen niet beschikbaar',
        'message': 'De wisselkoersen konden niet worden opgehaald van de ECB.',
        'suggestion': 'Controleer uw internetverbinding en probeer het opnieuw. '
                     'De ECB XML feed moet bereikbaar zijn.'
    },
    'ecb_timeout': {
        'title': 'ECB server timeout',
        'message': 'De ECB server reageert niet.',
        'suggestion': 'Probeer het later opnieuw.'
    },
    'ecb_connection_error': {
        'title': 'Geen verbinding met ECB',
        'message': 'Kan geen verbinding maken met de ECB server.',
        'suggestion': 'Controleer uw internetverbinding.'
    },
    'ecb_rate_missing': {
        'title': 'Wisselkoers niet gevonden',
        'message': 'De wisselkoers voor een specifieke datum kon niet worden gevonden.',
        'suggestion': 'Controleer of de transactiedatum correct is.'
    },
    'missing_rate': {
        'title': 'Wisselkoers ontbreekt',
        'message': 'Er ontbreekt een wisselkoers voor een van de transacties.',
        'suggestion': 'Controleer de transactiedata.'
    },
    'missing_currency_rate': {
        'title': 'Valutakoers ontbreekt',
        'message': 'De ECB heeft geen koers voor de opgegeven valuta.',
        'suggestion': 'Controleer of de valuta correct is geëxtraheerd.'
    },
    'processing_error': {
        'title': 'Verwerkingsfout',
        'message': 'Er is een fout opgetreden tijdens het verwerken van de statements.',
        'suggestion': 'Probeer het opnieuw. Als het probleem aanhoudt, neem contact op met ondersteuning.'
    },
    'library_missing': {
        'title': 'Ontbrekende software',
        'message': 'Een vereiste bibliotheek is niet geïnstalleerd.',
        'suggestion': 'Voer uit: pip install pdfplumber openpyxl reportlab requests'
    },
    'extraction_failed': {
        'title': 'Extractie mislukt',
        'message': 'De transacties konden niet worden geëxtraheerd uit de PDF.',
        'suggestion': 'Controleer of het PDF-formaat correct is.'
    }
}


def get_error_response(error_type: str, details: str = None) -> dict:
    """Get standardized error response"""
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['processing_error'])
    return {
        'error': True,
        'error_type': error_type,
        'title': error_info['title'],
        'message': error_info['message'],
        'suggestion': error_info['suggestion'],
        'details': details
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def cleanup_files(paths: list):
    """Clean up temporary files"""
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass  # Ignore cleanup errors


def get_system_status() -> dict:
    """Get system status for diagnostics"""
    return {
        'pdf_library': PDF_LIBRARY or 'Not installed',
        'pdf_available': PDF_LIBRARY is not None,
        'reportlab_available': REPORTLAB_AVAILABLE,
        'upload_folder': str(app.config['UPLOAD_FOLDER']),
        'output_folder': str(app.config['OUTPUT_FOLDER']),
    }


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    """Main page with upload form"""
    system_status = get_system_status()
    return render_template('index.html', system_status=system_status)


@app.route('/upload', methods=['POST'])
def upload_files():
    """
    Handle PDF uploads and process TOB calculations
    
    Returns:
        Redirect to results page on success
        Redirect to index with error flash on failure
    """
    uploaded_paths = []
    
    try:
        # Check if files were uploaded
        if 'pdfs' not in request.files:
            flash_error('no_files')
            return redirect(url_for('index'))
        
        files = request.files.getlist('pdfs')
        
        if not files or all(f.filename == '' for f in files):
            flash_error('no_files')
            return redirect(url_for('index'))
        
        # Validate and save uploaded files
        valid_files = []
        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    valid_files.append(file)
                else:
                    flash(f'Bestand "{file.filename}" is geen PDF en wordt overgeslagen.', 'warning')
        
        if not valid_files:
            flash_error('invalid_files')
            return redirect(url_for('index'))
        
        # Save files to upload folder
        for file in valid_files:
            filename = secure_filename(file.filename)
            # Add timestamp to prevent overwrites
            timestamp_prefix = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filepath = app.config['UPLOAD_FOLDER'] / f"{timestamp_prefix}{filename}"
            file.save(str(filepath))
            uploaded_paths.append(str(filepath))
        
        # Process statements
        try:
            results = process_statements(uploaded_paths)
        except ExtractionError as e:
            flash_error(e.error_type, str(e))
            cleanup_files(uploaded_paths)
            return redirect(url_for('index'))
        
        # Generate output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_base = app.config['OUTPUT_FOLDER'] / f'tob_report_{timestamp}'
        
        excel_path = f'{output_base}.xlsx'
        csv_path = f'{output_base}.csv'
        md_path = f'{output_base}.md'
        
        generate_excel(results, excel_path)
        generate_csv(results, csv_path)
        generate_markdown(results, md_path)
        
        # Generate PDF if available
        pdf_path = None
        if REPORTLAB_AVAILABLE:
            pdf_path = f'{output_base}.pdf'
            try:
                generate_pdf(results, pdf_path)
            except Exception as e:
                app.logger.warning(f"PDF generation failed: {e}")
                pdf_path = None
        
        # Clean up uploaded files
        cleanup_files(uploaded_paths)
        
        # Store results metadata
        results_meta = {
            'timestamp': timestamp,
            'generated_at': datetime.now().isoformat(),
            'transaction_count': len(results['transactions']),
            'total_eur': results['total_eur'],
            'total_tob': results['total_tob'],
            'brokers': results.get('brokers', []),
            'warnings': results.get('warnings', []),
            'files': {
                'excel': os.path.basename(excel_path),
                'csv': os.path.basename(csv_path),
                'markdown': os.path.basename(md_path),
                'pdf': os.path.basename(pdf_path) if pdf_path else None
            },
            'transactions': results['transactions']  # Store for display
        }
        
        meta_path = app.config['OUTPUT_FOLDER'] / f'results_{timestamp}.json'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(results_meta, f, indent=2, ensure_ascii=False, default=str)
        
        flash(f'Berekening voltooid: {len(results["transactions"])} transacties verwerkt.', 'success')
        return redirect(url_for('results', timestamp=timestamp))
    
    except ExtractionError as e:
        app.logger.error(f"Extraction error: {e}")
        flash_error(e.error_type, str(e))
        cleanup_files(uploaded_paths)
        return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Unexpected error: {traceback.format_exc()}")
        flash_error('processing_error', str(e))
        cleanup_files(uploaded_paths)
        return redirect(url_for('index'))


def flash_error(error_type: str, details: str = None):
    """Flash an error message with proper formatting"""
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['processing_error'])
    message = f"<strong>{error_info['title']}</strong><br>{error_info['message']}"
    if details:
        message += f"<br><small class='text-muted'>Details: {details}</small>"
    message += f"<br><em>{error_info['suggestion']}</em>"
    flash(message, 'error')


@app.route('/results/<timestamp>')
def results(timestamp):
    """Show calculation results"""
    try:
        meta_path = app.config['OUTPUT_FOLDER'] / f'results_{timestamp}.json'
        
        if not meta_path.exists():
            flash('Resultaten niet gevonden. Mogelijk zijn ze verlopen.', 'error')
            return redirect(url_for('index'))
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            results_data = json.load(f)
        
        return render_template('results.html', 
                             results=results_data, 
                             timestamp=timestamp)
    
    except json.JSONDecodeError:
        flash('Resultaatbestand is beschadigd.', 'error')
        return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Error loading results: {e}")
        flash(f'Fout bij laden resultaten: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download/<timestamp>/<filetype>')
def download(timestamp, filetype):
    """Download generated files"""
    try:
        meta_path = app.config['OUTPUT_FOLDER'] / f'results_{timestamp}.json'
        
        if not meta_path.exists():
            flash('Resultaten niet gevonden.', 'error')
            return redirect(url_for('index'))
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            results_data = json.load(f)
        
        # Map filetype to file info
        file_mapping = {
            'excel': {
                'key': 'excel',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'fallback_ext': '.xlsx'
            },
            'csv': {
                'key': 'csv',
                'mimetype': 'text/csv; charset=utf-8',
                'fallback_ext': '.csv'
            },
            'pdf': {
                'key': 'pdf',
                'mimetype': 'application/pdf',
                'fallback_ext': '.pdf'
            },
            'markdown': {
                'key': 'markdown',
                'mimetype': 'text/markdown; charset=utf-8',
                'fallback_ext': '.md'
            }
        }
        
        if filetype not in file_mapping:
            flash('Ongeldig bestandstype.', 'error')
            return redirect(url_for('results', timestamp=timestamp))
        
        file_info = file_mapping[filetype]
        filename = results_data.get('files', {}).get(file_info['key'])
        
        if not filename:
            flash(f'{filetype.upper()} bestand niet beschikbaar.', 'error')
            return redirect(url_for('results', timestamp=timestamp))
        
        filepath = app.config['OUTPUT_FOLDER'] / filename
        
        if not filepath.exists():
            flash('Bestand niet gevonden.', 'error')
            return redirect(url_for('results', timestamp=timestamp))
        
        return send_file(
            str(filepath),
            mimetype=file_info['mimetype'],
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        app.logger.error(f"Download error: {e}")
        flash(f'Fout bij downloaden: {str(e)}', 'error')
        return redirect(url_for('results', timestamp=timestamp))


@app.route('/about')
def about():
    """About page with calculation methodology"""
    system_status = get_system_status()
    return render_template('about.html', system_status=system_status)


@app.route('/api/status')
def api_status():
    """API endpoint for system status (useful for debugging)"""
    return jsonify({
        'status': 'ok',
        'system': get_system_status(),
        'supported_brokers': ['Interactive Brokers', 'Saxo Bank'],
        'tob_rate': '0.35%',
        'max_tob_per_transaction': '€ 1,600'
    })


@app.route('/api/validate', methods=['POST'])
def api_validate():
    """
    API endpoint to validate a PDF without full processing
    Useful for checking if a file will be recognized
    """
    if 'pdf' not in request.files:
        return jsonify({'valid': False, 'error': 'No file provided'})
    
    file = request.files['pdf']
    
    if not file or not allowed_file(file.filename):
        return jsonify({'valid': False, 'error': 'Invalid file type'})
    
    try:
        # Save temporarily
        filename = secure_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / f"validate_{filename}"
        file.save(str(filepath))
        
        # Try to read and detect broker
        text = extract_text_from_pdf(str(filepath))
        broker = detect_broker(text)
        
        # Clean up
        os.remove(filepath)
        
        if broker == Broker.UNKNOWN:
            return jsonify({
                'valid': False,
                'error': 'Unknown broker format',
                'broker': None
            })
        
        return jsonify({
            'valid': True,
            'broker': broker.value,
            'text_length': len(text)
        })
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        })


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('Bestand is te groot. Maximum grootte is 50MB.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error"""
    app.logger.error(f"Internal error: {traceback.format_exc()}")
    flash('Er is een interne fout opgetreden. Probeer het opnieuw.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(e):
    """Handle page not found"""
    return render_template('404.html'), 404


# =============================================================================
# TEMPLATE FILTERS
# =============================================================================

@app.template_filter('belgian_number')
def belgian_number_filter(value, decimals=2):
    """Jinja2 filter for Belgian number formatting"""
    if value is None:
        return ""
    try:
        value = float(value)
        if decimals == 0:
            int_part = int(round(value))
            return f"{int_part:,}".replace(',', '.')
        else:
            int_part = int(value)
            dec_part = round(value - int_part, decimals)
            int_str = f"{int_part:,}".replace(',', '.')
            dec_str = f"{dec_part:.{decimals}f}"[1:].replace('.', ',')
            return int_str + dec_str
    except (ValueError, TypeError):
        return str(value)


@app.template_filter('eur')
def eur_filter(value):
    """Jinja2 filter for EUR formatting"""
    return f"€ {belgian_number_filter(value)}"


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def open_browser():
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Development server
    print("=" * 60)
    print("Belgian TOB Tax Calculator")
    print("=" * 60)
    print(f"PDF Library: {PDF_LIBRARY or 'NOT INSTALLED'}")
    print(f"PDF Generation: {'Available' if REPORTLAB_AVAILABLE else 'Not available'}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
    print("=" * 60)
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1.5, open_browser).start()    
        
    app.run(debug=True, host='127.0.0.1', port=5000)
