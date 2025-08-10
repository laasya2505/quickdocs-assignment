-- sample_data.sql
-- Insert Processes
INSERT OR IGNORE INTO processes (name, description, status) VALUES 
('Home Loan Application', 'Complete home loan application process', 'active'),
('KYC Verification', 'Know Your Customer verification process', 'active');

-- Insert Document Types
INSERT OR IGNORE INTO document_types (name, description, required_fields) VALUES 
('PAN Card', 'Permanent Account Number card', '{"pan_number": "string", "name": "string", "father_name": "string"}'),
('Salary Slip', 'Monthly salary slip', '{"employer_name": "string", "gross_salary": "number", "month_year": "string"}'),
('Bank Statement', '6-month bank statement', '{"account_number": "string", "bank_name": "string", "average_balance": "number"}'),
('Aadhaar Card', 'Unique identification card', '{"aadhaar_number": "string", "name": "string", "address": "string"}'),
('Property Documents', 'Property ownership documents', '{"property_value": "number", "location": "string", "document_type": "string"}');

-- Insert Customers
INSERT OR IGNORE INTO customers (name, email, phone) VALUES 
('Rajesh Kumar', 'rajesh.kumar@email.com', '9876543210'),
('Priya Sharma', 'priya.sharma@email.com', '9876543211'),
('Amit Singh', 'amit.singh@email.com', '9876543212'),
('Sunita Gupta', 'sunita.gupta@email.com', '9876543213'),
('Vikram Patel', 'vikram.patel@email.com', '9876543214');

-- Set up process requirements
INSERT OR IGNORE INTO process_document_requirements (process_id, document_type_id, is_mandatory) VALUES 
(1, 1, 1),  -- Home Loan requires PAN Card
(1, 2, 1),  -- Home Loan requires Salary Slip
(1, 3, 1),  -- Home Loan requires Bank Statement
(1, 5, 1),  -- Home Loan requires Property Documents
(2, 1, 1),  -- KYC requires PAN Card
(2, 4, 1);  -- KYC requires Aadhaar Card

-- Assign customers to processes
INSERT OR IGNORE INTO process_assignments (customer_id, process_id, status, completion_percentage) VALUES 
(1, 1, 'pending', 25),   -- Rajesh for Home Loan
(2, 1, 'pending', 75),   -- Priya for Home Loan
(3, 2, 'completed', 100), -- Amit for KYC
(4, 1, 'pending', 50),    -- Sunita for Home Loan (Updated to 50%)
(5, 2, 'pending', 50);   -- Vikram for KYC

-- Sample document submissions (Complete with Sunita's data)
INSERT OR IGNORE INTO document_submissions (customer_id, process_id, document_type_id, file_url, ocr_extracted_data, validation_status) VALUES 
-- Rajesh Kumar - Home Loan (25% complete - 1/4 documents)
(1, 1, 1, '/uploads/rajesh_pan.pdf', '{"pan_number": "ABCDE1234F", "name": "Rajesh Kumar", "father_name": "Suresh Kumar"}', 'approved'),

-- Priya Sharma - Home Loan (75% complete - 3/4 documents)
(2, 1, 1, '/uploads/priya_pan.pdf', '{"pan_number": "FGHIJ5678K", "name": "Priya Sharma", "father_name": "Ramesh Sharma"}', 'approved'),
(2, 1, 2, '/uploads/priya_salary.pdf', '{"employer_name": "Tech Corp India Pvt Ltd", "gross_salary": "75000", "month_year": "July 2025"}', 'approved'),
(2, 1, 3, '/uploads/priya_bank.pdf', '{"account_number": "123456789", "bank_name": "State Bank of India", "average_balance": "150000"}', 'approved'),

-- Amit Singh - KYC (100% complete - 2/2 documents)
(3, 2, 1, '/uploads/amit_pan.pdf', '{"pan_number": "KLMNO9012P", "name": "Amit Singh", "father_name": "Vijay Singh"}', 'approved'),
(3, 2, 4, '/uploads/amit_aadhaar.pdf', '{"aadhaar_number": "1234-5678-9012", "name": "Amit Singh", "address": "123 Main Street, Mumbai"}', 'approved'),

-- Sunita Gupta - Home Loan (50% complete - 2/4 documents) [ADDED]
(4, 1, 1, '/uploads/sunita_pan.pdf', '{"pan_number": "UVWXY7890Z", "name": "Sunita Gupta", "father_name": "Mohan Gupta"}', 'approved'),
(4, 1, 2, '/uploads/sunita_salary.pdf', '{"employer_name": "Global Tech Solutions", "gross_salary": "65000", "month_year": "July 2025"}', 'approved'),

-- Vikram Patel - KYC (50% complete - 1/2 documents)
(5, 2, 1, '/uploads/vikram_pan.pdf', '{"pan_number": "PQRST3456U", "name": "Vikram Patel", "father_name": "Kiran Patel"}', 'approved');
