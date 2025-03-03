import React from 'react';

function ResultDisplay({ result }) {
  return (
    <div className="result-display">
      <h2>Analysis Results</h2>
      
      {/* Show the SQL query that Gemini generated */}
      {result.sql_query && (
        <div className="sql-query">
          <h3>Generated SQL Query:</h3>
          <pre>{result.sql_query}</pre>
        </div>
      )}
      
      {/* Show Gemini's explanation of the results */}
      {result.explanation && (
        <div className="explanation">
          <h3>Data Analysis:</h3>
          <p>{result.explanation}</p>
        </div>
      )}
      
      {/* Show the actual data in a table */}
      {result.data && (
        <div className="data">
          <h3>Data Results:</h3>
          <div className="data-table">
            {result.data.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    {Object.keys(result.data[0]).map((header) => (
                      <th key={header}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.data.map((row, index) => (
                    <tr key={index}>
                      {Object.values(row).map((value, i) => (
                        <td key={i}>{value}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No matching data found</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultDisplay; 