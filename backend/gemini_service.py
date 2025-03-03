import os
from dotenv import load_dotenv
import google.generativeai as genai
from database import execute_query, save_conversation, get_recent_conversations, get_all_tables
import re

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def clean_sql_query(sql):
    """Clean the SQL query by removing markdown formatting and extra whitespace"""
    # Remove markdown SQL code block if present
    sql = sql.replace('```sql', '').replace('```', '')
    # Remove any leading/trailing whitespace
    sql = sql.strip()
    return sql

def is_valid_query(question):
    """Basic validation of user input"""
    # Check if question is too short or random characters
    if len(question) < 3:
        return False, "Please ask a more detailed question"
    
    # Check if question contains too many special characters
    special_chars = re.findall(r'[^a-zA-Z0-9\s\?\.,]', question)
    if len(special_chars) > len(question) * 0.3:  # If more than 30% are special chars
        return False, "Your question contains too many special characters. Please rephrase it."
    
    # Check for common SQL injection patterns
    sql_patterns = ['drop', 'delete', 'truncate', ';', '--', 'union']
    if any(pattern in question.lower() for pattern in sql_patterns):
        return False, "Invalid question format. Please ask a natural language question."
    
    return True, ""

def process_question(question):
    try:
        # Validate input
        is_valid, error_message = is_valid_query(question)
        if not is_valid:
            return {
                'error': error_message,
                'suggestion': "Try asking something like: 'What are the total sales?' or 'Show me orders from January 2024'"
            }

        # Get schemas of all tables
        schemas = get_all_tables()
        if not schemas:
            return {
                'error': 'No data tables available',
                'suggestion': 'Please upload some data files first.'
            }
        
        # Format schema information for prompt
        schema_str = "\n".join([
            f"Table: {table_name}\n" +
            "\n".join([f"  {col}: {dtype}" for col, dtype in table_schema.items()])
            for table_name, table_schema in schemas.items()
        ])
        
        # Enhanced prompt for better query generation
        prompt = f"""
        Given these database tables and their schemas:
        {schema_str}
        
        And this user question: "{question}"
        
        If the question seems invalid or unclear, respond with "INVALID_QUERY" and a helpful message.
        Otherwise, generate a SQL query to answer the question.
        Make sure to use proper table names and JOIN operations if needed.
        """
        
        # Generate SQL query using Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        sql_response = response.text.strip()
        
        # Check if Gemini detected an invalid query
        if sql_response.startswith("INVALID_QUERY"):
            return {
                'error': sql_response.replace("INVALID_QUERY", "").strip(),
                'suggestion': "Try being more specific or check for typos."
            }
        
        # Clean and execute the SQL query
        sql_query = clean_sql_query(sql_response)
        
        # Execute the query
        result_df = execute_query(sql_query)
        
        # If no results found
        if result_df.empty:
            return {
                'error': 'No data found matching your query',
                'sql_query': sql_query,
                'suggestion': 'Try modifying your search criteria'
            }
        
        # Generate explanation
        format_prompt = f"""
        Given this data:
        {result_df.to_string()}
        
        Provide a clear, concise explanation of these results in response to the question: "{question}"
        If the results seem unexpected or potentially incorrect, mention that in your explanation.
        Focus on the key insights and important numbers in the data.
        """
        
        explanation = model.generate_content(format_prompt).text
        
        return {
            'data': result_df.to_dict('records'),
            'explanation': explanation,
            'sql_query': sql_query
        }
    except Exception as e:
        print(f"Error in process_question: {str(e)}")
        return {
            'error': 'Sorry, I had trouble understanding that question.',
            'suggestion': 'Try rephrasing your question or being more specific.'
        } 