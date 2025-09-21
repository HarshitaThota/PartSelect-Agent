import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";

function ChatWindow() {

  const defaultMessage = [{
    role: "assistant",
    content: "👋 Hi! I'm your PartSelect AI assistant. I can help you find refrigerator and dishwasher parts, check compatibility, provide installation guides, and troubleshoot issues. What can I help you with today?"
  }];

  const [messages,setMessages] = useState(defaultMessage)
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
      scrollToBottom();
  }, [messages]);

  const handleSend = async (input) => {
    if (input.trim() !== "" && !isLoading) {
      // Set user message
      setMessages(prevMessages => [...prevMessages, { role: "user", content: input }]);
      setInput("");
      setIsLoading(true);

      // Call API & set assistant message
      const newMessage = await getAIMessage(input);
      setMessages(prevMessages => [...prevMessages, newMessage]);
      setIsLoading(false);
    }
  };

  return (
      <div className="chat-window">
          <div className="chat-header">
              <h3>PartSelect AI Assistant</h3>
              <p>Expert help for refrigerator & dishwasher parts</p>
          </div>

          <div className="messages-container">
              {messages.map((message, index) => (
                  <div key={index} className={`${message.role}-message-container`}>
                      {message.content && (
                          <div className={`message ${message.role}-message`}>
                              <div dangerouslySetInnerHTML={{__html: marked(message.content).replace(/<p>|<\/p>/g, "")}}></div>
                          </div>
                      )}
                  </div>
              ))}
              {isLoading && (
                <div className="assistant-message-container">
                  <div className="message assistant-message loading-message">
                    <div className="typing-indicator">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about parts, installation, compatibility, or troubleshooting..."
              onKeyPress={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  handleSend(input);
                  e.preventDefault();
                }
              }}
            />
            <button
              className="send-button"
              onClick={() => handleSend(input)}
              disabled={isLoading}
            >
              {isLoading ? "Thinking..." : "Send"}
            </button>
          </div>
      </div>
);
}

export default ChatWindow;
