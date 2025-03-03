import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000';

function ChatInterface({ data }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const suggestionQuestions = [
    "What are the total sales in 2024?",
    "Show me the best-selling products",
    "What is the average order value?",
    "Compare January and February sales"
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const timeoutId = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timeoutId);
  }, [messages]);

  const scrollToBottom = () => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ 
        behavior: "smooth",
        block: "end",
      });
    }
  };

  const handleSuggestionClick = (question) => {
    setInputMessage(question);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const userMessage = inputMessage.trim();
    
    if (!userMessage) return;
    
    setInputMessage('');
    setShowSuggestions(false);
    
    // Add user message to chat
    setMessages(prev => [...prev, {
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    }]);

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        question: userMessage
      });

      if (response.data.error) {
        // Handle error with suggestions
        setMessages(prev => [...prev, {
          type: 'error',
          content: {
            message: response.data.error,
            suggestion: response.data.suggestion
          },
          timestamp: new Date()
        }]);
      } else {
        // Handle successful response
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: {
            sql: response.data.sql_query,
            explanation: response.data.explanation,
            data: response.data.data
          },
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: {
          message: 'Failed to process your question',
          suggestion: 'Please try asking in a different way or check your question for typos.'
        },
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatValue = (value) => {
    if (typeof value === 'number') {
      if (String(value).includes('.')) {
        return `$${value.toFixed(2)}`;
      }
      return value;
    }
    return value;
  };

  const renderDataTable = (data) => {
    if (!data || data.length === 0) return null;
    
    const columns = Object.keys(data[0]);
    
    return (
      <div className="data-table">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column.replace(/_/g, ' ').toUpperCase()}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                {columns.map((column) => (
                  <td key={column}>{formatValue(row[column])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row-count">
          Total rows: {data.length}
        </div>
      </div>
    );
  };

  const renderMessage = (message) => {
    if (message.type === 'assistant') {
      return (
        <div className="message-content">
          <div className="sql-query">
            <div className="section-header">
              <h4>Generated SQL</h4>
              <button 
                className="copy-btn"
                onClick={() => navigator.clipboard.writeText(message.content.sql)}
              >
                Copy
              </button>
            </div>
            <pre>{message.content.sql}</pre>
          </div>
          <div className="explanation">
            <h4>Analysis</h4>
            <p>{message.content.explanation}</p>
          </div>
          {message.content.data && (
            <div className="results">
              <h4>Results</h4>
              {renderDataTable(message.content.data)}
            </div>
          )}
        </div>
      );
    }
    // ... rest of the message rendering logic
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>Data Analysis Chat</h3>
        <div className="chat-actions">
          <button 
            className="clear-chat"
            onClick={() => setMessages([])}
            disabled={messages.length === 0}
          >
            Clear Chat
          </button>
        </div>
      </div>

      <div className="chat-messages" style={{ position: 'relative' }}>
        {showSuggestions && messages.length === 0 && (
          <div className="suggestions">
            <h4>Suggested Questions</h4>
            <div className="suggestion-buttons">
              {suggestionQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(question)}
                  className="suggestion-btn"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.type}`}
          >
            <div className="message-header">
              <span className="message-sender">
                {message.type === 'user' ? 'You' : 'DataChat AI'}
              </span>
              <span className="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </span>
            </div>
            
            {message.type === 'user' ? (
              <div className="message-content">
                {message.content}
              </div>
            ) : message.type === 'assistant' ? (
              renderMessage(message)
            ) : (
              <div className="message-content error">
                <p>{message.content.message}</p>
                {message.content.suggestion && (
                  <div className="error-suggestion">
                    <p>💡 Suggestion:</p>
                    <p>{message.content.suggestion}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message assistant loading">
            <div className="loading-indicator">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              Processing your question...
            </div>
          </div>
        )}
        <div ref={chatEndRef} style={{ height: '1px', width: '100%' }} />
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          ref={inputRef}
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask a question about your data..."
          className="chat-input"
          disabled={loading}
        />
        <button 
          type="submit" 
          className="chat-submit-btn"
          disabled={loading}
        >
          <span>Send</span>
          <svg viewBox="0 0 24 24" className="send-icon">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </form>
    </div>
  );
}

export default ChatInterface; 