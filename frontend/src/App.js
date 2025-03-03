import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import UploadPrompt from './components/UploadPrompt';
import './App.css';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000';

function App() {
  const [uploadedData, setUploadedData] = useState({
    tables: [],
    schema: null
  });
  const [error, setError] = useState(null);

  const handleFileSelect = async (file, type) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      let endpoint = type === 'remove' 
        ? `${API_BASE_URL}/remove/${encodeURIComponent(file.name)}`
        : `${API_BASE_URL}/upload/csv`;

      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      
      if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      if (type === 'remove') {
        setUploadedData(prev => ({
          ...prev,
          tables: prev.tables.filter(t => t !== file.name),
          schema: response.data.schema
        }));
      } else {
        setUploadedData(prev => ({
          tables: [...prev.tables, file.name],
          schema: response.data.schema
        }));
      }
      setError(null);
    } catch (error) {
      console.error('Error handling file:', error);
      setError(error.response?.data?.error || 'Network error: Unable to connect to server');
    }
  };

  return (
    <div className="App">
      {uploadedData.tables.length === 0 ? (
        <UploadPrompt onFileSelect={handleFileSelect} error={error} />
      ) : (
        <ChatInterface 
          uploadedData={uploadedData}
          onFileRemove={handleFileSelect}
        />
      )}
    </div>
  );
}

export default App; 