import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './Dashboard';
import Podmioty from './Podmioty';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/podmioty" element={<Podmioty />} />
      </Routes>
    </Router>
  );
}

export default App;