from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import json
from datetime import datetime
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

DATABASE = 'quickdocs.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema and sample data"""
    if os.path.exists(DATABASE):
        print("Database file already exists. Removing...")
        os.remove(DATABASE)
    
    conn = get_db_connection()
    
    try:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        print("Reading schema file...")
        # Read and execute schema
        with open('database/schema.sql', 'r') as f:
            schema_content = f.read()
            print(f"Schema content length: {len(schema_content)} characters")
            conn.executescript(schema_content)
        
        print("Reading sample data file...")
        # Read and execute sample data
        with open('database/sample_data.sql', 'r') as f:
            data_content = f.read()
            print(f"Data content length: {len(data_content)} characters")
            conn.executescript(data_content)
        
        conn.commit()
        
        # Verify tables were created
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables created: {tables}")
        
        if 'process_assignments' not in tables:
            raise Exception("Critical table 'process_assignments' was not created!")
        
        print("Database initialized successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: Could not find SQL files: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Looking for files in: {os.path.abspath('database/')}")
        raise e
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Print the first 500 chars of problematic content for debugging
        try:
            with open('database/schema.sql', 'r') as f:
                content = f.read()
                print("Schema file content preview:")
                print(content[:500] + "..." if len(content) > 500 else content)
        except:
            pass
        raise e
    finally:
        conn.close()


@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response

@app.route('/')
def dashboard():
    """Enhanced Status Dashboard with OCR data preview"""
    try:
        conn = get_db_connection()
        
        query = '''
        SELECT 
            c.name as customer_name,
            p.name as process_name,
            pa.status,
            pa.completion_percentage,
            COALESCE((SELECT COUNT(*) FROM document_submissions ds 
                     WHERE ds.customer_id = pa.customer_id AND ds.process_id = pa.process_id), 0) as documents_submitted,
            COALESCE((SELECT COUNT(*) FROM process_document_requirements pdr 
                     WHERE pdr.process_id = pa.process_id AND pdr.is_mandatory = 1), 0) as documents_required,
            -- Get latest document submission with OCR data
            (SELECT GROUP_CONCAT(dt.name || ': ' || 
                    CASE 
                        WHEN ds.ocr_extracted_data IS NOT NULL 
                        THEN 'Extracted'
                        ELSE 'Pending'
                    END, ', ')
             FROM document_submissions ds
             JOIN document_types dt ON ds.document_type_id = dt.id
             WHERE ds.customer_id = pa.customer_id AND ds.process_id = pa.process_id
            ) as document_status
        FROM process_assignments pa
        JOIN customers c ON pa.customer_id = c.id
        JOIN processes p ON pa.process_id = p.id
        ORDER BY pa.assignment_date DESC
        '''
        
        assignments = conn.execute(query).fetchall()
        conn.close()
        
        return render_template('dashboard.html', assignments=assignments)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', assignments=[])



@app.route('/customers')
def customers():
    conn = get_db_connection()
    
    # This pulls from your customers table sample data
    customers = conn.execute('SELECT * FROM customers ORDER BY registration_date DESC').fetchall()
    
    # This pulls from your processes table sample data  
    processes = conn.execute('SELECT * FROM processes WHERE status = "active"').fetchall()
    
    return render_template('customers.html', customers=customers, processes=processes)


@app.route('/add_customer', methods=['POST'])
def add_customer():
    """Add new customer and optionally assign to process"""
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    process_id = request.form.get('process_id')
    
    conn = get_db_connection()
    
    try:
        # Insert customer
        cursor = conn.execute(
            'INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)',
            (name, email, phone)
        )
        customer_id = cursor.lastrowid
        
        # Assign to process if selected
        if process_id:
            conn.execute(
                'INSERT INTO process_assignments (customer_id, process_id) VALUES (?, ?)',
                (customer_id, process_id)
            )
        
        conn.commit()
        flash('Customer added successfully!', 'success')
        
    except sqlite3.IntegrityError:
        flash('Customer with this email already exists!', 'error')
    except Exception as e:
        flash(f'Error adding customer: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('customers'))

@app.route('/documents')
def documents():
    """Document Submission Page"""
    try:
        conn = get_db_connection()
        
        # Get customers with active assignments
        customers = conn.execute('''
            SELECT DISTINCT c.id, c.name 
            FROM customers c
            JOIN process_assignments pa ON c.id = pa.customer_id
            WHERE pa.status = 'pending'
        ''').fetchall()
        
        document_types = conn.execute('SELECT * FROM document_types').fetchall()
        
        conn.close()
        return render_template('documents.html', customers=customers, document_types=document_types)
    
    except Exception as e:
        flash(f'Error loading documents page: {str(e)}', 'error')
        return render_template('documents.html', customers=[], document_types=[])

@app.route('/get_customer_processes/<int:customer_id>')
def get_customer_processes(customer_id):
    """Get processes for a specific customer (AJAX endpoint)"""
    try:
        conn = get_db_connection()
        
        processes = conn.execute('''
            SELECT p.id, p.name 
            FROM processes p
            JOIN process_assignments pa ON p.id = pa.process_id
            WHERE pa.customer_id = ? AND pa.status = 'pending'
        ''', (customer_id,)).fetchall()
        
        conn.close()
        
        return jsonify([{'id': p['id'], 'name': p['name']} for p in processes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit_document', methods=['POST'])
def submit_document():
    """Submit a document"""
    customer_id = request.form['customer_id']
    process_id = request.form['process_id']
    document_type_id = request.form['document_type_id']
    file_url = request.form['file_url']
    
    # Simulate OCR extracted data
    extracted_data = {}
    for key, value in request.form.items():
        if key.startswith('extracted_'):
            field_name = key.replace('extracted_', '')
            extracted_data[field_name] = value
    
    conn = get_db_connection()
    
    try:
        # Check if document already submitted
        existing = conn.execute('''
            SELECT id FROM document_submissions 
            WHERE customer_id = ? AND process_id = ? AND document_type_id = ?
        ''', (customer_id, process_id, document_type_id)).fetchone()
        
        if existing:
            flash('Document already submitted for this process!', 'error')
        else:
            conn.execute('''
                INSERT INTO document_submissions 
                (customer_id, process_id, document_type_id, file_url, ocr_extracted_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, process_id, document_type_id, file_url, json.dumps(extracted_data)))
            
            # Update completion percentage
            update_completion_percentage(conn, customer_id, process_id)
            
            conn.commit()
            flash('Document submitted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error submitting document: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('documents'))
@app.route('/edit_customer/<int:customer_id>')
def edit_customer(customer_id):
    """Edit customer form"""
    conn = get_db_connection()
    
    try:
        customer = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()
        processes = conn.execute('SELECT * FROM processes WHERE status = "active"').fetchall()
        
        # Get current assignment
        current_assignment = conn.execute('''
            SELECT pa.process_id 
            FROM process_assignments pa 
            WHERE pa.customer_id = ?
        ''', (customer_id,)).fetchone()
        
        if not customer:
            flash('Customer not found!', 'error')
            return redirect(url_for('customers'))
        
        return render_template('edit_customer.html', 
                             customer=customer, 
                             processes=processes,
                             current_assignment=current_assignment)
    except Exception as e:
        flash(f'Error loading customer: {str(e)}', 'error')
        return redirect(url_for('customers'))
    finally:
        conn.close()

@app.route('/update_customer/<int:customer_id>', methods=['POST'])
def update_customer(customer_id):
    """Update customer details"""
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    process_id = request.form.get('process_id')
    
    conn = get_db_connection()
    
    try:
        # Update customer
        conn.execute(
            'UPDATE customers SET name = ?, email = ?, phone = ? WHERE id = ?',
            (name, email, phone, customer_id)
        )
        
        # Update process assignment if changed
        if process_id:
            # Remove existing assignment
            conn.execute('DELETE FROM process_assignments WHERE customer_id = ?', (customer_id,))
            # Add new assignment
            conn.execute(
                'INSERT INTO process_assignments (customer_id, process_id) VALUES (?, ?)',
                (customer_id, process_id)
            )
        
        conn.commit()
        flash('Customer updated successfully!', 'success')
        
    except sqlite3.IntegrityError:
        flash('Email already exists for another customer!', 'error')
    except Exception as e:
        flash(f'Error updating customer: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('customers'))

@app.route('/delete_customer/<int:customer_id>')
def delete_customer(customer_id):
    """Delete customer and related data"""
    conn = get_db_connection()
    
    try:
        # Get customer name for confirmation message
        customer = conn.execute('SELECT name FROM customers WHERE id = ?', (customer_id,)).fetchone()
        
        if not customer:
            flash('Customer not found!', 'error')
            return redirect(url_for('customers'))
        
        # Delete related records first (to maintain referential integrity)
        conn.execute('DELETE FROM document_submissions WHERE customer_id = ?', (customer_id,))
        conn.execute('DELETE FROM process_assignments WHERE customer_id = ?', (customer_id,))
        conn.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        
        conn.commit()
        flash(f'Customer "{customer["name"]}" deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('customers'))

def update_completion_percentage(conn, customer_id, process_id):
    """Calculate and update completion percentage for a process assignment"""
    
    # Get required documents count
    required_count = conn.execute('''
        SELECT COUNT(*) as count
        FROM process_document_requirements 
        WHERE process_id = ? AND is_mandatory = 1
    ''', (process_id,)).fetchone()['count']
    
    # Get submitted documents count
    submitted_count = conn.execute('''
        SELECT COUNT(DISTINCT document_type_id) as count
        FROM document_submissions 
        WHERE customer_id = ? AND process_id = ?
    ''', (customer_id, process_id)).fetchone()['count']
    
    # Calculate percentage
    percentage = int((submitted_count / required_count) * 100) if required_count > 0 else 0
    status = 'completed' if percentage == 100 else 'pending'
    
    # Update assignment
    conn.execute('''
        UPDATE process_assignments 
        SET completion_percentage = ?, status = ?
        WHERE customer_id = ? AND process_id = ?
    ''', (percentage, status, customer_id, process_id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Check if we need to initialize database
    if not os.path.exists(DATABASE):
        print("Database not found. Creating new database...")
        init_db()
    else:
        print("Database found. Starting application...")
    
    print(f"Starting Flask application...")
    print(f"Database location: {os.path.abspath(DATABASE)}")
    print(f"Access the application at: http://localhost:5000")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
