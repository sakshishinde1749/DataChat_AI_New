from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv
from database import create_table_from_file, init_database
from gemini_service import process_question
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
            model = genai.GenerativeModel('gemini-1.5-flash')
            sql_prompt = f"""
            Given these database tables and their structure:
            {schema_str}

            Write a comprehensive SQL query to answer this question: "{question}"
            
            Requirements:
            1. Use LEFT JOINs when counting or summing to include rows with zero values
            2. Include meaningful column names using AS for better readability
            3. Format numeric values properly (especially prices)
            4. Order results in a logical way (e.g., alphabetically for names, descending for amounts)
            5. Only use the tables and columns shown above
            
            Return only the raw SQL query without any markdown formatting or explanation.
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
            Given this data:
            {results}
            
            And the original question: "{question}"
            
            Provide a comprehensive analysis following these guidelines:
            1. Start with a clear summary of the key findings
            2. Include specific numbers and calculations where relevant
            3. Format currency values with dollar signs and two decimal places
            4. Mention any interesting patterns or outliers
            5. If there are missing or zero values, explain their significance
            6. Keep the explanation clear and concise, but thorough
            
            Focus on insights that directly answer the question while providing relevant context.
            """
            
            explanation = model.generate_content(explanation_prompt).text
            
            # Format numeric columns in results
            formatted_results = []
            for row in results:
                formatted_row = {}
                for key, value in row.items():
                    if isinstance(value, (int, float)) and 'price' in key.lower() or 'total' in key.lower() or 'amount' in key.lower():
                        formatted_row[key] = f"${value:.2f}"
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