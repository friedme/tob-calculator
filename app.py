"""
Belgian TOB Tax Calculator - Flask Web Application
Calculates Tax on Stock Exchange Transactions from broker statements
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our calculation modules
from tob_calculator import process_statements, generate_excel, generate_csv, generate_pdf

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle PDF uploads and process TOB calculations"""
    if 'pdfs' not in request.files:
        flash('No files uploaded', 'error')
        return redirect(url_for('index'))
    
    files = request.files.getlist('pdfs')
    
    if not files or files[0].filename == '':
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    # Save uploaded files
    uploaded_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_paths.append(filepath)
    
    if not uploaded_paths:
        flash('No valid PDF files uploaded', 'error')
        return redirect(url_for('index'))
    
    try:
        logger.info(f"Processing {len(uploaded_paths)} PDF files")
        # Process statements and calculate TOB
        results = process_statements(uploaded_paths)
        logger.info(f"Successfully extracted {len(results.get('transactions', []))} transactions")

        # Check if any transactions were extracted
        if not results['transactions'] or len(results['transactions']) == 0:
            flash('⚠️ No transactions were extracted from the uploaded PDFs. Please verify you uploaded the correct statement type. See the About page for instructions on downloading the correct broker statements.', 'warning')
            # Clean up uploaded files
            for path in uploaded_paths:
                if os.path.exists(path):
                    os.remove(path)
            return redirect(url_for('index'))

        # Generate output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_path = os.path.join(app.config['OUTPUT_FOLDER'], f'tob_report_{timestamp}.xlsx')
        csv_path = os.path.join(app.config['OUTPUT_FOLDER'], f'tob_report_{timestamp}.csv')
        pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], f'tob_summary_{timestamp}.pdf')

        generate_excel(results, excel_path)
        generate_csv(results, csv_path)
        generate_pdf(results, pdf_path)
        
        # Clean up uploaded files
        for path in uploaded_paths:
            os.remove(path)
        
        # Store results in session-like manner (simplified for demo)
        with open(os.path.join(app.config['OUTPUT_FOLDER'], f'results_{timestamp}.json'), 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'total_transactions': len(results['transactions']),
                'total_eur': results['total_eur'],
                'total_tob': results['total_tob'],
                'excel_file': os.path.basename(excel_path),
                'csv_file': os.path.basename(csv_path),
                'pdf_file': os.path.basename(pdf_path),
                'transactions': results['transactions']  # Store full transaction data
            }, f)
        
        return redirect(url_for('results', timestamp=timestamp))
    
    except Exception as e:
        logger.error(f"Error processing statements: {str(e)}", exc_info=True)
        flash(f'Error processing statements: {str(e)}', 'error')
        # Clean up uploaded files on error
        for path in uploaded_paths:
            if os.path.exists(path):
                os.remove(path)
        return redirect(url_for('index'))

@app.route('/results/<timestamp>')
def results(timestamp):
    """Show calculation results"""
    try:
        results_file = os.path.join(app.config['OUTPUT_FOLDER'], f'results_{timestamp}.json')
        with open(results_file, 'r') as f:
            results = json.load(f)
        return render_template('results.html', results=results, timestamp=timestamp)
    except FileNotFoundError:
        flash('Results not found', 'error')
        return redirect(url_for('index'))

@app.route('/download/<timestamp>/<filetype>')
def download(timestamp, filetype):
    """Download generated files"""
    try:
        results_file = os.path.join(app.config['OUTPUT_FOLDER'], f'results_{timestamp}.json')
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        if filetype == 'excel':
            filename = results['excel_file']
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filetype == 'csv':
            filename = results['csv_file']
            mimetype = 'text/csv'
        elif filetype == 'pdf':
            filename = results['pdf_file']
            mimetype = 'application/pdf'
        else:
            flash('Invalid file type', 'error')
            return redirect(url_for('results', timestamp=timestamp))
        
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=filename)
    
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('results', timestamp=timestamp))

@app.route('/about')
def about():
    """About page with calculation methodology"""
    return render_template('about.html')

@app.route('/api/transaction-details/<timestamp>')
def transaction_details(timestamp):
    """API endpoint to get transaction details as JSON"""
    try:
        results_file = os.path.join(app.config['OUTPUT_FOLDER'], f'results_{timestamp}.json')
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        return json.dumps({
            'transactions': results.get('transactions', []),
            'total_eur': results['total_eur'],
            'total_tob': results['total_tob']
        }), 200, {'Content-Type': 'application/json'}
    
    except Exception as e:
        return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)