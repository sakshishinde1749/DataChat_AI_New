from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv
from database import create_table_from_file, init_database
from gemini_service import is_valid_query
import traceback
from werkzeug.utils import secure_filename

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

app = Flask(__name__)

# Configure CORS to allow requests from your frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],  # Your frontend URL
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
    }
})

DATABASE = 'data.db'

def init_db():
    """Initialize database connection"""
    try:
        # Use absolute path to the database file
        db_path = os.path.join(os.path.dirname(__file__), DATABASE)
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def get_table_schema():
    """Get detailed schema information for all tables"""
    schema = {}
    try:
        with init_db() as conn:
            cursor = conn.cursor()
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                schema[table_name] = {
                    'columns': [col[1] for col in columns],
                    'types': [col[2] for col in columns]
                }
        return schema
    except Exception as e:
        print(f"Error getting schema: {str(e)}")
        return {}

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "Server is running",
        "app": "DataChat AI"
    }), 200

@app.route('/upload/csv', methods=['POST'])
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            print(f"Received file: {filename}")
            
            # Create DataFrame from CSV
            df = pd.read_csv(file)
            
            # Get table name from filename (without extension)
            table_name = os.path.splitext(filename)[0]
            
            # Create table in database
            create_table_from_file(df, table_name)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'table': table_name
            })
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/remove/<filename>', methods=['POST'])
def remove_file(filename):
    try:
        table_name = os.path.splitext(filename)[0]
        with init_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        
        schema = get_table_schema()
        return jsonify({'message': 'File removed successfully', 'schema': schema})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/query', methods=['POST'])
def process_query():
    try:
        data = request.json
        if not data or 'question' not in data:
            return jsonify({
                'error': 'No question provided',
                'suggestion': 'Please provide a question to analyze'
            }), 400

        question = data['question']
        print(f"Processing question: {question}")

        # Validate the question first
        is_valid, error_message = is_valid_query(question)
        if not is_valid:
            return jsonify({
                'error': error_message,
                'suggestion': "Try asking something like: 'What are the total sales?' or 'Show me orders from January 2024'"
            }), 400

        # Get current schema with error checking
        try:
            schema = get_table_schema()
            print("Schema retrieved:", schema)
        except Exception as e:
            print(f"Error getting schema: {str(e)}")
            return jsonify({
                'error': 'Database error',
                'suggestion': 'There was an error accessing the database'
            }), 500

        if not schema:
            return jsonify({
                'error': 'No tables found in database',
                'suggestion': 'Please upload some data files first'
            }), 400

        # Format schema for the prompt
        schema_str = ""
        for table_name, table_info in schema.items():
            if table_name not in ['conversation_history', 'sqlite_sequence', 'data']:
                schema_str += f"\nTable: {table_name}\n"
                for col, col_type in zip(table_info['columns'], table_info['types']):
                    schema_str += f"  - {col} ({col_type})\n"

        # Generate SQL query using Gemini
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            sql_prompt = f"""
            Given these database tables and their structure:
            {schema_str}

            Write a SQL query to answer this question: "{question}"

            Analysis Guidelines:
            1. Schema Analysis:
               - Examine table relationships through foreign key columns
               - Understand data types and their meaning:
                 * Percentage fields (like discounts) are stored as numbers (e.g., 10 means 10%)
                 * Price/monetary fields need decimal precision
                 * Dates may need formatting
               - Identify required tables and their relationships

            2. Data Operations:
               - For calculations with percentages:
                 * Always divide percentage values by 100
                 * Example: 10% should be calculated as value/100
                 * Use (1 - discount/100) for discount calculations
               - For monetary calculations:
                 * Use ROUND() for consistent decimal places
                 * Maintain proper calculation order
               - For counting and aggregations:
                 * Choose appropriate functions (SUM, AVG, COUNT)
                 * Group results as needed
                 * Use LEFT JOIN when counting from reference tables
                 * Include all records from main entity
                - For table relationships:
                 * ALWAYS use LEFT JOIN from primary entity to preserve all records
                 * Start FROM the table containing all records needed (e.g., customers for customer queries)
                 * Chain additional LEFT JOINs for related data
                 * Use COALESCE/IFNULL for NULL values (e.g., COALESCE(SUM(...), 0))
                 * Show zero/empty values for missing data

            3. Query Structure:
              - Start with the main entity table
              - Use LEFT JOIN (not regular JOIN) to preserve all records
              - Apply filters in WHERE clause after joins
              - Group by main entity identifiers
              - Order results meaningfully

            4. Result Formatting:
               - Use clear column aliases
               - Ensure proper ordering
               - Format output for readability
               - Include supporting metrics when:
                 * Counting items (show the count)
                 * Finding maximums (show the value)
                 * Calculating totals (show the total)
                 * Comparing data (show relevant measures)
               - Name columns descriptively (e.g., number_of_orders instead of count)
               - For empty results:
                 * Return meaningful message instead of empty set
                 * Show relevant thresholds or criteria
                 * Indicate why no results were found
               - Include all relevant information in results

            Generate a focused SQL query that provides complete information to answer the question.
            Return only the SQL query, no explanations.
            """

            print("Sending SQL prompt to Gemini:", sql_prompt)
            response = model.generate_content(sql_prompt)
            sql_query = response.text.strip()
            
            # Clean the SQL query
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            print("Generated SQL query:", sql_query)

            # Execute the query with error handling
            with init_db() as conn:
                df = pd.read_sql_query(sql_query, conn)
                print("Query executed successfully, row count:", len(df))
                
            if df.empty:
                return jsonify({
                    'error': 'No results found',
                    'sql_query': sql_query,
                    'suggestion': 'Try modifying your question'
                }), 404

            # Format results for explanation
            results = df.to_dict('records')
            
            # Generate detailed explanation
            explanation_prompt = f"""
            Based on the original question: "{question}"

            And the SQL query used to retrieve the data: {sql_query}
            
            And the result data retrieved: {results}

            Provide a clear analysis that:
            1. Directly answers the question with key insights and findings
            2. Uses proper markdown formatting for better readability:
               - Use bullet points for listing items
               - Use tables for structured data when relevant
               - Use bold and italics for emphasis
            3. Formats numbers appropriately:
               - Currency with ₹ and two decimal places
               - Percentages with two decimal places
               - Large numbers with comma separators
            4. Provides relevant context or trends when helpful
            
            Keep the focus on answering the user's question clearly and concisely.
            Only mention SQL or technical details if there's a specific issue that affects the results.
            """
            
            explanation = model.generate_content(explanation_prompt).text
            
            # Format numeric columns in results
            formatted_results = []
            for row in results:
                formatted_row = {}
                for key, value in row.items():
                    # Only format as currency if it's a monetary value
                    if isinstance(value, (int, float)):
                        key_lower = key.lower()
                        # Check specifically for monetary columns
                        if ('price' in key_lower or 
                            'amount' in key_lower or 
                            'sales' in key_lower or
                            'revenue' in key_lower or 
                            'spent' in key_lower or 
                            'cost' in key_lower):
                            formatted_row[key] = f"₹{value:.2f}"
                        else:
                            # Keep other numeric values as is (like quantity)
                            formatted_row[key] = value
                    else:
                        formatted_row[key] = value
                formatted_results.append(formatted_row)
            
            return jsonify({
                'sql_query': sql_query,
                'data': formatted_results,
                'explanation': explanation,
                'row_count': len(df)
            })

        except Exception as e:
            print(f"SQL execution error: {str(e)}")
            return jsonify({
                'error': 'Error executing the query',
                'sql_query': sql_query,
                'suggestion': 'There might be an issue with the generated SQL query'
            }), 400

    except Exception as e:
        print(f"General error in process_query: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to process your question',
            'suggestion': 'Please try asking in a different way or check your question for typos'
        }), 400

if __name__ == '__main__':
    # Initialize database
    init_database()
    # Explicitly bind to all interfaces
    app.run(host='127.0.0.1', port=5000, debug=True) 