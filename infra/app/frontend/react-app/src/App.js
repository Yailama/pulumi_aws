import React, { useState, useEffect } from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  // useState hook to manage the status
  const [status, setStatus] = useState(null);

  // useEffect hook to make the API call once the component mounts
  useEffect(() => {
    // Calling the backend API
    fetch("/api/docs/")
      .then(response => {
        if (response.status === 200) {
          setStatus('success');
        } else {
          setStatus('error');
        }
      })
      .catch(error => {
        console.error("There was an error fetching from the backend", error);
        setStatus('error');
      });
  }, []);  // The empty array [] means this useEffect runs once when the component mounts.

  return (
    <div className="App">
      <header className="App-header">
        <div>
        <p> This is react page to test application !</p>
        If you see this, that means that:
        <ul>
        <li> React app has been successfully launched</li>
        <li> Load balancer successfully routes you to application</li>
        </ul>
        </div>
        <div>
        Backend check status:
        {/* Conditionally render status bar based on the status */}
        {status === 'success' ? (
          <div style={{ width: '100%', height: '20px', backgroundColor: 'green' }}>Status: OK</div>
        ) : status === 'error' ? (
          <div style={{ width: '100%', height: '20px', backgroundColor: 'red' }}>Status: Error</div>
        ) : null}
        You can run tests of services using <a href="/api/docs/">Swagger</a>
        </div>
      </header>
    </div>
  );
}

export default App;
