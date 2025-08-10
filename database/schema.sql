CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    required_fields TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS process_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    process_id INTEGER NOT NULL,
    assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (process_id) REFERENCES processes(id),
    UNIQUE(customer_id, process_id)
);

CREATE TABLE IF NOT EXISTS document_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    process_id INTEGER NOT NULL,
    document_type_id INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_url VARCHAR(255),
    ocr_extracted_data TEXT,
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'approved', 'rejected')),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (document_type_id) REFERENCES document_types(id)
);

CREATE TABLE IF NOT EXISTS process_document_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL,
    document_type_id INTEGER NOT NULL,
    is_mandatory BOOLEAN DEFAULT 1,
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (document_type_id) REFERENCES document_types(id),
    UNIQUE(process_id, document_type_id)
);
