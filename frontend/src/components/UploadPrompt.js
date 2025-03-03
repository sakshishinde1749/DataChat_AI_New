import React, { useState } from 'react';

function UploadPrompt({ onFileSelect, error: parentError }) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFiles = (files) => {
    setError(null);
    
    const validFiles = files.filter(file => {
      const fileType = file.name.split('.').pop().toLowerCase();
      return ['csv', 'pdf'].includes(fileType);
    });

    if (validFiles.length !== files.length) {
      setError('Some files were skipped. Only CSV and PDF files are supported.');
    }

    const newFiles = [...uploadedFiles];
    validFiles.forEach(file => {
      if (!uploadedFiles.some(f => f.name === file.name)) {
        newFiles.push(file);
      }
    });

    setUploadedFiles(newFiles);
  };

  const removeFile = async (fileToRemove) => {
    try {
      // Call backend to remove the file's table
      await onFileSelect(fileToRemove, 'remove');
      setUploadedFiles(uploadedFiles.filter(file => file !== fileToRemove));
    } catch (error) {
      setError('Failed to remove file: ' + error.message);
    }
  };

  const handleUpload = async () => {
    if (uploadedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    try {
      // Upload all files
      for (const file of uploadedFiles) {
        const fileType = file.name.split('.').pop().toLowerCase();
        await onFileSelect(file, fileType);
      }
    } catch (error) {
      setError('Upload failed: ' + error.message);
    }
  };

  return (
    <div className="upload-prompt">
      <div className="upload-content">
        <h2>Welcome to DataChat AI</h2>
        <p>Upload your data files to start the analysis</p>
        
        <div className="upload-zone"
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            multiple
            accept=".csv,.pdf"
            onChange={(e) => handleFiles(Array.from(e.target.files))}
            className="file-input"
          />
          <span>Drop your files here or click to browse</span>
        </div>

        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            <h3>Selected Files</h3>
            {uploadedFiles.map((file, index) => (
              <div key={index} className="file-item">
                <span>{file.name}</span>
                <button onClick={() => removeFile(file)}>Remove</button>
              </div>
            ))}
            <button className="upload-button" onClick={handleUpload}>
              Upload Files
            </button>
          </div>
        )}

        {(error || parentError) && (
          <div className="upload-error">
            {error || parentError}
          </div>
        )}

        <div className="upload-info">
          <h4>Features</h4>
          <ul>
            <li>CSV Data Analysis</li>
            <li>PDF Text Extraction</li>
            <li>Natural Language Queries</li>
            <li>Smart Data Insights</li>
            <li>Interactive Visualizations</li>
            <li>Context-Aware Responses</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default UploadPrompt; 