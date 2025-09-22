import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../services/api";
import { marked } from "marked";
import PartCard from "./PartCard";

function ChatWindow({ addToCart, cartItems }) {

  const defaultMessage = [{
    role: "assistant",
    content: "Hi! I'm your PartSelect AI assistant. I can help you find refrigerator and dishwasher parts, check compatibility, provide installation guides, troubleshoot issues, and assist with purchases. What can I help you with today?"
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

      try {
        // Call API & set assistant message
        const newMessage = await getAIMessage(input);

        // Ensure the response has the expected format
        const formattedMessage = {
          role: "assistant",
          content: newMessage.message || "I'm sorry, I couldn't process your request.",
          parts: newMessage.parts || []
        };

        setMessages(prevMessages => [...prevMessages, formattedMessage]);
      } catch (error) {
        console.error('Error getting AI response:', error);
        const errorMessage = {
          role: "assistant",
          content: "I'm sorry, I'm having trouble connecting to the server. Please try again."
        };
        setMessages(prevMessages => [...prevMessages, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleAddToCart = async (part) => {
    try {
      const success = await addToCart(part);

      if (success) {
        // Add a success message to the chat
        const successMessage = {
          role: "assistant",
          content: `Successfully added **${part.name}** to your cart! Would you like to continue shopping or proceed to checkout?`
        };
        setMessages(prevMessages => [...prevMessages, successMessage]);
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
      const errorMessage = {
        role: "assistant",
        content: `Sorry, I couldn't add ${part.name} to your cart. Please try again.`
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    }
  };

  const handleViewDetails = (part) => {
    const detailMessage = {
      role: "assistant",
      content: `Here are the details for **${part.name}** (${part.partselect_number}):\n\n**Brand:** ${part.brand}\n**Price:** $${part.price}\n**Availability:** ${part.in_stock ? 'In Stock' : 'Out of Stock'}\n\n${part.description || 'No additional description available.'}\n\nWould you like installation instructions, compatibility information, or help with purchasing?`
    };
    setMessages(prevMessages => [...prevMessages, detailMessage]);
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
                      {message.parts && message.parts.length > 0 && (
                          <div className="parts-container">
                              {message.parts.map((part, partIndex) => (
                                  <PartCard
                                      key={`${index}-${partIndex}`}
                                      part={part}
                                      onAddToCart={handleAddToCart}
                                      onViewDetails={handleViewDetails}
                                      isInCart={cartItems.some(item => item.partselect_number === part.partselect_number)}
                                  />
                              ))}
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
