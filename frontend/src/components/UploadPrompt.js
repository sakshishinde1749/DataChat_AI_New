import React, { useState, useEffect } from 'react';

function UploadPrompt({ onFileSelect, error: parentError, onBackToChat, uploadedData }) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Reset selected files state when component mounts
  useEffect(() => {
    setSelectedFiles([]);
    setError(null);
    setUploading(false);
  }, []);

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
      return ['csv'].includes(fileType);
    });

    if (validFiles.length !== files.length) {
      setError('Some files were skipped. Only CSV files are supported.');
    }

    const newFiles = [...selectedFiles];
    validFiles.forEach(file => {
      if (!selectedFiles.some(f => f.name === file.name)) {
        newFiles.push(file);
      }
    });

    setSelectedFiles(newFiles);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      for (const file of selectedFiles) {
        await onFileSelect(file, 'upload');
      }
      setSelectedFiles([]);
    } catch (error) {
      setError('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  const removeFile = (fileToRemove) => {
    setSelectedFiles(prev => prev.filter(file => file !== fileToRemove));
  };

  const handleRemoveUploaded = async (fileName) => {
    try {
      // Create a dummy file object with the name
      const fileObj = new File([""], fileName, { type: "text/csv" });
      await onFileSelect(fileObj, 'remove');
    } catch (error) {
      setError('Failed to remove file: ' + error.message);
    }
  };

  return (
    <div className="upload-prompt">
      <div className="upload-content">
        <div className="upload-header">
          <h2>Upload Your Data Files</h2>
          {onBackToChat && (
            <button className="back-to-chat" onClick={onBackToChat}>
              Back to Chat
            </button>
          )}
        </div>

        {/* Show already uploaded files if any */}
        {uploadedData?.tables?.length > 0 && (
          <div className="uploaded-files current">
            <h3>Current Files</h3>
            {uploadedData.tables.map((fileName, index) => (
              <div key={index} className="file-item">
                <span>{fileName}</span>
                <button 
                  onClick={() => handleRemoveUploaded(fileName)}
                  className="remove-file"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <p>Upload additional data files</p>
        
        {/* Drop zone for new files */}
        <div 
          className={`upload-zone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-input"
            multiple
            accept=".csv"
            onChange={(e) => handleFiles(Array.from(e.target.files))}
            style={{ display: 'none' }}
          />
          <label htmlFor="file-input">
            <div className="option-icon">📁</div>
            <div>Drop CSV files here or click to select</div>
            <span>Supported format: CSV</span>
          </label>
        </div>

        {/* Show newly selected files */}
        {selectedFiles.length > 0 && (
          <div className="uploaded-files new">
            <h3>Selected Files</h3>
            {selectedFiles.map((file, index) => (
              <div key={index} className="file-item">
                <span>{file.name}</span>
                <button onClick={() => removeFile(file)}>Remove</button>
              </div>
            ))}
            <button 
              className="upload-button" 
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? 'Uploading...' : 'Upload Files'}
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
            <li>Natural Language Queries</li>
            <li>Smart Data Insights</li>
            <li>Interactive Visualizations</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default UploadPrompt; 