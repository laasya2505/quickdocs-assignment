QuickDocs - Document Collection System with AI Query Interface
A proof-of-concept document collection system for loan applications with AI-powered natural language querying capabilities.

📋 Table of Contents
Technologies Used

Setup Instructions

How to Run the Application

Project Structure

Natural Language Query System

Database Schema

Usage Examples

Error Handling

🛠 Technologies Used
Backend
Python 3.11+ - Core programming language

Flask 2.3.3 - Web framework for the application

SQLite3 - Database for data storage

sqlite3 - Python database interface

Frontend
HTML5 - Page structure and content

CSS3 - Styling and responsive design

JavaScript (ES6) - Dynamic interactions and AJAX calls

Jinja2 - Template engine for dynamic HTML rendering

AI/NLP Components
Regular Expressions - Pattern matching for natural language queries

JSON Processing - Handling OCR extracted data

Rule-based NLP - Converting natural language to SQL queries

Development Tools
VSCode - Integrated development environment

Git - Version control

SQLite Browser - Database management

🚀 Setup Instructions
Prerequisites
Python 3.11 or higher

pip (Python package installer)

Git (optional, for cloning)

1. Project Setup
bash
# Create and navigate to project directory
mkdir quickdocs-assignment
cd quickdocs-assignment

# Create project structure
mkdir -p application/templates application/static/{css,js}
mkdir -p database nl_query docs application/screenshots
2. Python Environment
bash
# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required packages
pip install flask
3. Database Setup
bash
# Ensure you have the required SQL files:
# - database/schema.sql (table creation scripts)
# - database/sample_data.sql (sample data insertion)
4. File Structure
text
quickdocs-assignment/
├── README.md
├── application/
│   ├── app.py
│   ├── requirements.txt
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── customers.html
│       ├── documents.html
│       ├── edit_customer.html
│       ├── 404.html
│       └── 500.html
├── database/
│   ├── schema.sql
│   └── sample_data.sql
├── nl_query/
│   ├── query_interface.py
│   └── query_examples.txt
└── quickdocs.db (auto-generated)
▶️ How to Run the Application
1. Start the Flask Application
bash
# Navigate to project root
cd quickdocs-assignment

# Run the Flask application
python3 application/app.py
2. Access the Web Interface
Open your browser and navigate to: http://localhost:5000

The application will automatically create the database on first run

3. Run Natural Language Query Interface
bash
# In a separate terminal, navigate to project root
cd quickdocs-assignment

# Run the NL query interface
python3 nl_query/query_interface.py
4. Application URLs
Dashboard: http://localhost:5000/ (Process status overview)

Customers: http://localhost:5000/customers (Customer management)

Documents: http://localhost:5000/documents (Document submission)

🧠 Natural Language Query System
How NL to SQL Conversion Works
The system uses rule-based pattern matching to convert natural language queries into SQL:

1. Query Processing Flow
python
User Input → Text Preprocessing → Pattern Matching → SQL Generation → Database Execution → Results
2. Pattern Matching Examples
python
# Pattern for customer queries
{
    'pattern': r'show (?:all )?(?:the )?customers?',
    'sql': 'SELECT id, name, email, phone FROM customers ORDER BY registration_date DESC'
}

# Pattern with parameter extraction
{
    'pattern': r'how many documents (?:has|have) (.+?) submitted',
    'sql_template': '''SELECT c.name, COUNT(ds.id) as document_count
                      FROM customers c
                      LEFT JOIN document_submissions ds ON c.id = ds.customer_id
                      WHERE LOWER(c.name) LIKE LOWER('%{}%')
                      GROUP BY c.id, c.name'''
}
3. Supported Query Types
Show all customers - Lists all registered customers

List all pending processes - Shows processes with pending assignments

How many documents has [name] submitted? - Document count per customer

Which process has the most documents? - Process with highest submissions

Which customers are assigned to [process]? - Customer assignments per process

Show completed processes - Lists completed assignments

List all document types - Available document categories

Show pending document submissions - Unvalidated documents

Count customers by process - Customer distribution across processes

Show customer [name] details - Individual customer information

Example of Successful Queries
Query 1: Customer Information
text
Input: "Show all customers"
Generated SQL: SELECT id, name, email, phone, registration_date FROM customers ORDER BY registration_date DESC
Results: 6 customers found
- Rajesh Kumar (rajesh.kumar@email.com)
- Priya Sharma (priya.sharma@email.com)
- Amit Singh (amit.singh@email.com)
- Sunita Gupta (sunita.gupta@email.com)
- Vikram Patel (vikram.patel@email.com)
Query 2: Document Count
text
Input: "How many documents has Rajesh Kumar submitted?"
Generated SQL: SELECT c.name, COUNT(ds.id) as document_count FROM customers c LEFT JOIN document_submissions ds ON c.id = ds.customer_id WHERE LOWER(c.name) LIKE LOWER('%rajesh kumar%') GROUP BY c.id, c.name
Results: Rajesh Kumar: 1 documents
Query 3: Process Analysis
text
Input: "Which process has the most documents?"
Generated SQL: SELECT p.name, COUNT(ds.id) as document_count FROM processes p LEFT JOIN document_submissions ds ON p.id = ds.process_id GROUP BY p.id, p.name ORDER BY document_count DESC LIMIT 1
Results: Home Loan Application: 4 documents
⚠️ Error Handling
Natural Language Query Errors
Example: Unrecognized Query Pattern
text
Input: "Tell me about the weather"
Output: 
Generated SQL: 
Explanation: Error processing query: Could not understand the query: 'tell me about the weather'
No results found.

Suggested queries:
- Show all customers
- List all pending processes
- How many documents has [customer name] submitted?
Example: SQL Execution Error
python
def _execute_query(self, sql_query: str) -> List[Dict]:
    try:
        cursor.execute(sql_query)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []
Web Application Error Handling
Database Connection Errors
python
@app.route('/')
def dashboard():
    try:
        conn = get_db_connection()
        # ... database operations
        return render_template('dashboard.html', assignments=assignments)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', assignments=[])
Form Validation Errors
python
@app.route('/add_customer', methods=['POST'])
def add_customer():
    try:
        # ... customer creation logic
        flash('Customer added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Customer with this email already exists!', 'error')
    except Exception as e:
        flash(f'Error adding customer: {str(e)}', 'error')
📊 Database Schema
The system uses a normalized SQLite database with the following entities:

processes - Loan application processes (Home Loan, KYC)

customers - Customer information and registration details

document_types - Available document categories with OCR field definitions

process_assignments - Links customers to processes with completion tracking

document_submissions - Uploaded documents with OCR extracted data

process_document_requirements - Defines required documents per process

🔧 Development Notes
Key Features Implemented
✅ CRUD Operations - Complete customer management

✅ Dynamic OCR Fields - Document-specific form fields

✅ Progress Tracking - Automatic completion percentage calculation

✅ Natural Language Queries - 10+ supported query patterns

✅ Error Handling - Comprehensive error management

✅ Responsive Design - Clean, professional UI

Known Limitations
OCR simulation only (no actual image processing)

Rule-based NLP (no external AI/ML services)

SQLite database (suitable for demo, not production scale)

No user authentication (as per assignment requirements)

📈 Future Enhancements
Integration with actual OCR services (Google Cloud Vision, AWS Textract)

AI-powered natural language processing (OpenAI GPT, Claude)

RESTful API endpoints for external integrations

Real file upload and storage management

Advanced analytics and reporting dashboards

Multi-tenant architecture for different organizations
