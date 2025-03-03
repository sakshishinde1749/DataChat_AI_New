import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000';

function QueryInput({ setResult, setLoading }) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        question: query
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('Query response:', response.data);
      
      if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      setResult(response.data);
      setError(null);
    } catch (error) {
      console.error('Error processing query:', error);
      setError(error.response?.data?.error || 'Failed to process your question. Please try again.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="query-input">
      <h2>Ask Questions About Your Data</h2>
      <p className="query-hint">
        Example questions:
        <br />
        - "What are the orders made in 2024?"
        <br />
        - "Show me total sales by month"
        <br />
        - "What is the average order value?"
      </p>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your question about the data..."
          className="query-input-field"
        />
        <button type="submit" className="query-submit-btn">
          Get Data
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}

export default QueryInput; 