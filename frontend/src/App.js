import React, { useState, useEffect } from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";
import CartModal from "./components/CartModal";
import { addToCart as apiAddToCart } from './services/api';

function App() {
  const [cartItems, setCartItems] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);
  const [lastOrderId, setLastOrderId] = useState(null);

  // Load cart from localStorage on component mount
  useEffect(() => {
    const savedCart = localStorage.getItem('partselect_cart');
    if (savedCart) {
      try {
        setCartItems(JSON.parse(savedCart));
      } catch (error) {
        console.error('Error loading cart from localStorage:', error);
      }
    }
  }, []);

  // Save cart to localStorage whenever cartItems changes
  useEffect(() => {
    localStorage.setItem('partselect_cart', JSON.stringify(cartItems));
  }, [cartItems]);

  const addToCart = async (part) => {
    try {
      // Call backend API
      await apiAddToCart(part.partselect_number, 1);

      // Update local cart
      setCartItems(prevItems => {
        const existingItem = prevItems.find(item => item.partselect_number === part.partselect_number);

        if (existingItem) {
          return prevItems.map(item =>
            item.partselect_number === part.partselect_number
              ? { ...item, quantity: item.quantity + 1 }
              : item
          );
        } else {
          return [...prevItems, { ...part, quantity: 1 }];
        }
      });

      return true;
    } catch (error) {
      console.error('Error adding to cart:', error);
      return false;
    }
  };

  const updateCartQuantity = (index, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(index);
      return;
    }

    setCartItems(prevItems =>
      prevItems.map((item, i) =>
        i === index ? { ...item, quantity: newQuantity } : item
      )
    );
  };

  const removeFromCart = (index) => {
    setCartItems(prevItems => prevItems.filter((_, i) => i !== index));
  };

  const handleCheckout = async () => {
    // Generate order ID
    const orderId = `PS${Date.now()}`;

    // Simulate checkout process
    return new Promise((resolve) => {
      setTimeout(() => {
        setLastOrderId(orderId);
        setOrderComplete(true);
        setCartItems([]); // Clear cart
        setIsCartOpen(false);

        // Auto-hide order confirmation after 5 seconds
        setTimeout(() => {
          setOrderComplete(false);
        }, 5000);

        resolve();
      }, 1500);
    });
  };

  const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
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
            <div className="customer-service">
              <div className="service-info">
                <div className="service-phone">1-866-319-8402</div>
                <div className="service-hours">Mon-Sat 8am-8pm EST</div>
                <div className="service-email">customerservice@partselect.com</div>
              </div>
            </div>
            <div className="cart-section">
              <button
                className="cart-btn"
                onClick={() => setIsCartOpen(true)}
                aria-label="Open shopping cart"
              >
                <span className="cart-icon">🛒</span>
                {totalItems > 0 && (
                  <span className="cart-badge">{totalItems}</span>
                )}
              </button>
            </div>
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
              <div className="feature">Genuine OEM parts guaranteed to fit</div>
              <div className="feature">Free installation guides</div>
              <div className="feature">Expert repair instructions</div>
            </div>
          </div>
          <div className="chat-container">
            <ChatWindow addToCart={addToCart} cartItems={cartItems} />
          </div>
        </div>
      </main>

      {/* Cart Modal */}
      <CartModal
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cartItems={cartItems}
        onUpdateQuantity={updateCartQuantity}
        onRemoveItem={removeFromCart}
        onCheckout={handleCheckout}
      />

      {/* Order Confirmation */}
      {orderComplete && (
        <div className="order-confirmation-overlay">
          <div className="order-confirmation">
            <div className="success-icon">✓</div>
            <h2>Order Placed Successfully!</h2>
            <p>Thank you for your purchase. Your order has been confirmed.</p>
            <div className="order-details">
              <p><strong>Order ID:</strong> {lastOrderId}</p>
              <p><strong>Status:</strong> Processing</p>
              <p>You'll receive a confirmation email shortly with tracking information.</p>
            </div>
            <button
              className="close-confirmation-btn"
              onClick={() => setOrderComplete(false)}
            >
              Continue Shopping
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
