import sqlite3
import re
import json
from typing import Dict, List, Tuple

class NLQueryProcessor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.schema_info = self._get_schema_info()
    
    def _get_schema_info(self) -> Dict:
        """Get database schema information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            schema[table] = columns
        
        conn.close()
        return schema
    def _preprocess_query(self, query: str) -> str:
        """Clean and normalize the query for better pattern matching"""
        # Convert to lowercase
        query = query.lower().strip()
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Remove common words that don't affect meaning
        stop_words = ['the', 'a', 'an']
        words = query.split()
        filtered_words = []
        
        for word in words:
            # Keep stop words only if they're not between key terms
            if word not in stop_words:
                filtered_words.append(word)
            elif len(filtered_words) > 0 and filtered_words[-1] not in ['show', 'list', 'which', 'what', 'how']:
                filtered_words.append(word)
        
        return ' '.join(filtered_words)

    def process_query(self, nl_query: str) -> Tuple[str, List, str]:
        """Process natural language query and return SQL, results, and explanation"""
        try:
            # Preprocess the query
            cleaned_query = self._preprocess_query(nl_query)
            print(f"Original: '{nl_query}' -> Cleaned: '{cleaned_query}'")  # Debug
            
            sql_query = self._convert_nl_to_sql(cleaned_query)
            results = self._execute_query(sql_query)
            explanation = f"Converted query '{nl_query}' to SQL and found {len(results)} results."
            return sql_query, results, explanation
        except Exception as e:
            return "", [], f"Error processing query: {str(e)}"

    def process_query(self, nl_query: str) -> Tuple[str, List, str]:
        """
        Process natural language query and return SQL, results, and explanation
        """
        try:
            # Clean the input - remove punctuation that might interfere
            cleaned_query = nl_query.lower().strip()
            # Remove question marks and other punctuation that shouldn't be in search
            cleaned_query = cleaned_query.replace('?', '').replace('.', '').replace('!', '')
            
            sql_query = self._convert_nl_to_sql(cleaned_query)
            results = self._execute_query(sql_query)
            explanation = f"Converted query '{nl_query}' to SQL and found {len(results)} results."
            return sql_query, results, explanation
        except Exception as e:
            return "", [], f"Error processing query: {str(e)}"

    
    def _convert_nl_to_sql(self, query: str) -> str:
        """Convert natural language to SQL using pattern matching"""
    
        # Updated patterns with more flexibility
        patterns = [
            # More flexible customer pattern - handles "the", "all the", etc.
            {
                'pattern': r'show (?:all )?(?:the )?customers',
                'sql': 'SELECT id, name, email, phone, registration_date FROM customers ORDER BY registration_date DESC'
            },
            
            # More flexible pending processes pattern
            {
                'pattern': r'list (?:all )?(?:the )?pending processes',
                'sql': '''SELECT DISTINCT p.name, p.description 
                        FROM processes p 
                        JOIN process_assignments pa ON p.id = pa.process_id 
                        WHERE pa.status = 'pending' '''
            },
            
            # Flexible document count pattern
            {
                'pattern': r'how many documents (?:has|have) (.+?) submitted',
                'sql_template': '''SELECT c.name, COUNT(ds.id) as document_count
                                FROM customers c
                                LEFT JOIN document_submissions ds ON c.id = ds.customer_id
                                WHERE LOWER(c.name) LIKE LOWER('%{}%')
                                GROUP BY c.id, c.name'''
            },
            
            # Flexible process assignment pattern
            {
                'pattern': r'(?:which|what) customers are assigned to (.+)',
                'sql_template': '''SELECT c.name, c.email, pa.status, pa.completion_percentage
                                FROM customers c
                                JOIN process_assignments pa ON c.id = pa.customer_id
                                JOIN processes p ON pa.process_id = p.id
                                WHERE LOWER(p.name) LIKE LOWER('%{}%')'''
            },
            
            # Flexible most documents pattern
            {
                'pattern': r'(?:which|what) process has (?:the )?most documents',
                'sql': '''SELECT p.name, COUNT(ds.id) as document_count
                        FROM processes p
                        LEFT JOIN document_submissions ds ON p.id = ds.process_id
                        GROUP BY p.id, p.name
                        ORDER BY document_count DESC
                        LIMIT 1'''
            },
            
            # Additional useful patterns
            {
                'pattern': r'show (?:all )?(?:the )?completed processes',
                'sql': '''SELECT c.name as customer_name, p.name as process_name, pa.completion_percentage
                        FROM process_assignments pa
                        JOIN customers c ON pa.customer_id = c.id
                        JOIN processes p ON pa.process_id = p.id
                        WHERE pa.status = 'completed' '''
            },
            
            {
                'pattern': r'list (?:all )?(?:the )?document types',
                'sql': 'SELECT name, description FROM document_types ORDER BY name'
            },
            # Add pattern for completed processes
            {
                'pattern': r'(?:list|show) (?:all )?(?:the )?completed processes?',
                'sql': '''SELECT c.name as customer_name, p.name as process_name, 
                                pa.completion_percentage, pa.assignment_date
                        FROM process_assignments pa
                        JOIN customers c ON pa.customer_id = c.id
                        JOIN processes p ON pa.process_id = p.id
                        WHERE pa.status = 'completed' 
                        ORDER BY pa.assignment_date DESC'''
            },
            
            # Enhanced pending processes with customer names
            {
                'pattern': r'(?:list|show) (?:all )?(?:the )?pending processes?',
                'sql': '''SELECT c.name as customer_name, p.name as process_name, 
                                pa.completion_percentage, pa.assignment_date
                        FROM process_assignments pa
                        JOIN customers c ON pa.customer_id = c.id
                        JOIN processes p ON pa.process_id = p.id
                        WHERE pa.status = 'pending' 
                        ORDER BY pa.assignment_date DESC'''
            },
            
            # Process details only (without customer names)
            {
                'pattern': r'(?:list|show) (?:all )?process types?',
                'sql': '''SELECT DISTINCT p.name, p.description 
                        FROM processes p 
                        WHERE p.status = 'active'
                        ORDER BY p.name'''
            }
        
        ]

        
        # Try to match patterns
        for pattern_obj in patterns:
            pattern = pattern_obj['pattern']
            match = re.search(pattern, query)
            
            if match:
                if 'sql_template' in pattern_obj:
                    # Extract parameter and clean it
                    param = match.group(1).strip()
                    # Remove common punctuation that interferes with database queries
                    param = param.replace('?', '').replace('.', '').replace('!', '').strip()
                    return pattern_obj['sql_template'].format(param)
                else:
                    return pattern_obj['sql']
        
        # If no pattern matches
        raise ValueError(f"Could not understand the query: '{query}'")

    
    def _execute_query(self, sql_query: str) -> List[Dict]:
        """Execute SQL query and return results as list of dictionaries"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            print(f"Executing SQL: {sql_query}")  # Debug output
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]
            print(f"Query returned {len(results)} results")  # Debug output
            return results
        except Exception as e:
            print(f"SQL execution error: {e}")
            raise e
        finally:
            conn.close()

def main():
    """Command-line interface for testing"""
    processor = NLQueryProcessor('quickdocs.db')
    
    print("=== QuickDocs Natural Language Query Interface ===")
    print("Try queries like:")
    print("- Show all customers")
    print("- List all pending processes")
    print("- How many documents has Rajesh Kumar submitted?")
    print("- Which process has the most documents?")
    print("- Which customers are assigned to Home Loan Application?")
    print("\nType 'quit' to exit.\n")
    
    while True:
        query = input("Enter your query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
        
        sql, results, explanation = processor.process_query(query)
        
        print(f"\nGenerated SQL: {sql}")
        print(f"Explanation: {explanation}")
        
        if results:
            print("\nResults:")
            print("-" * 50)
            for i, result in enumerate(results, 1):
                print(f"{i}. {dict(result)}")
        else:
            print("\nNo results found.")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
