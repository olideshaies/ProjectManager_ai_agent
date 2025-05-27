import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Chat } from './components/Chat'
import { SessionTimer } from './components/SessionTimer'
import ScoreboardPage from './pages/ScoreboardPage'
import './App.css'

// Create a simple HomePage component to wrap existing content
const HomePage: React.FC = () => {
  return (
    <>
      <h1>Voice Chat & Task Timer</h1>
      <Chat />
      <SessionTimer />
    </>
  );
};

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <nav className="main-nav">
          <ul>
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/scoreboard">Scoreboard</Link>
            </li>
          </ul>
        </nav>

        <hr />

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/scoreboard" element={<ScoreboardPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
