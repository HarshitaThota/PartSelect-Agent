import React from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

function App() {
  return (
    <div className="App">
      {/* PartSelect Chat Agent Header */}
      <header className="partselect-header">
        <div className="header-top">
          <div className="logo-section">
            <div className="logo">
              <span className="logo-icon">P</span>
              <span className="logo-text">PartSelect</span>
            </div>
            <span className="tagline">AI Chat Assistant</span>
          </div>
          <div className="header-right">
            <div className="agent-info">
              <div className="agent-title">Smart Parts Assistant</div>
              <div className="agent-subtitle">Refrigerator & Dishwasher Expert</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="hero-section">
          <div className="hero-content">
            <h1>Ask Our AI Assistant</h1>
            <p>Get instant help finding parts, installation guides, and troubleshooting tips</p>
            <div className="features">
              <div className="feature">✓ Genuine OEM parts guaranteed to fit</div>
              <div className="feature">✓ Free installation guides</div>
              <div className="feature">✓ Expert repair instructions</div>
            </div>
          </div>
          <div className="chat-container">
            <ChatWindow/>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
