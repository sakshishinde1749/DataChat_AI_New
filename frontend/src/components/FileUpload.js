import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000';

function FileUpload({ setData }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    
    // Reset states
    setError(null);
    setUploadSuccess(false);
    
    // Validate file
    if (!file) {
      setError('Please select a file');
      return;
    }
    
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }
    
    setFile(file);
    const formData = new FormData();
    formData.append('file', file);

    try {
      // First check if server is running
      const healthCheck = await axios.get(`${API_BASE_URL}/`);
      console.log('Health check response:', healthCheck.data);
      
      console.log('Uploading file:', file.name);
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        withCredentials: false,
      });
      
      console.log('Upload response:', response.data);
      
      if (response.data.error) {
        throw new Error(response.data.error);
      }
      
      setData(response.data);
      setUploadSuccess(true);
      setError(null);
    } catch (error) {
      console.error('Error details:', error);
      
      if (error.code === 'ERR_NETWORK') {
        setError(`Cannot connect to server at ${API_BASE_URL}. Please make sure the backend server is running.`);
      } else {
        setError(error.response?.data?.error || error.message || 'Error uploading file. Please try again.');
      }
      
      setData(null);
      setUploadSuccess(false);
    }
  };

  return (
    <div className="file-upload">
      <h2>Upload your CSV file</h2>
      <div className="upload-container">
        <input 
          type="file" 
          accept=".csv"
          onChange={handleFileUpload}
          className="file-input"
        />
        {error && (
          <p className="error">
            Error: {error}
            <br />
            <small>
              Make sure:
              <br />
              1. The backend server is running (python app.py)
              <br />
              2. You're uploading a valid CSV file
              <br />
              3. Port 5000 is not being used by another application
            </small>
          </p>
        )}
        {uploadSuccess && (
          <p className="success">
            File uploaded successfully! You can now ask questions about your data.
          </p>
        )}
      </div>
    </div>
  );
}

export default FileUpload; 