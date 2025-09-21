import React, { useState } from 'react';
import './CartModal.css';

const CartModal = ({ isOpen, onClose, cartItems, onUpdateQuantity, onRemoveItem, onCheckout }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  if (!isOpen) return null;

  const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const shipping = subtotal >= 50 ? 0 : 15.99;
  const tax = subtotal * 0.085;
  const total = subtotal + shipping + tax;

  const handleCheckout = async () => {
    setIsProcessing(true);
    try {
      await onCheckout();
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="cart-modal-overlay" onClick={onClose}>
      <div className="cart-modal" onClick={e => e.stopPropagation()}>
        <div className="cart-header">
          <h2>Shopping Cart</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="cart-content">
          {cartItems.length === 0 ? (
            <div className="empty-cart">
              <p>Your cart is empty</p>
              <p>Add some parts from the chat to get started!</p>
            </div>
          ) : (
            <>
              <div className="cart-items">
                {cartItems.map((item, index) => (
                  <div key={index} className="cart-item">
                    <div className="item-info">
                      <h4>{item.name}</h4>
                      <p className="part-number">#{item.partselect_number}</p>
                      <p className="brand">{item.brand}</p>
                    </div>

                    <div className="item-controls">
                      <div className="quantity-controls">
                        <button
                          onClick={() => onUpdateQuantity(index, Math.max(1, item.quantity - 1))}
                          className="qty-btn"
                        >
                          -
                        </button>
                        <span className="quantity">{item.quantity}</span>
                        <button
                          onClick={() => onUpdateQuantity(index, item.quantity + 1)}
                          className="qty-btn"
                        >
                          +
                        </button>
                      </div>

                      <div className="item-price">
                        ${(item.price * item.quantity).toFixed(2)}
                      </div>

                      <button
                        onClick={() => onRemoveItem(index)}
                        className="remove-btn"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="cart-summary">
                <div className="summary-line">
                  <span>Subtotal:</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className="summary-line">
                  <span>Shipping:</span>
                  <span>{shipping === 0 ? 'FREE' : `$${shipping.toFixed(2)}`}</span>
                </div>
                <div className="summary-line">
                  <span>Tax:</span>
                  <span>${tax.toFixed(2)}</span>
                </div>
                <div className="summary-line total">
                  <span>Total:</span>
                  <span>${total.toFixed(2)}</span>
                </div>

                {subtotal < 50 && (
                  <div className="shipping-notice">
                    Add ${(50 - subtotal).toFixed(2)} more for free shipping!
                  </div>
                )}

                <button
                  className="checkout-btn"
                  onClick={handleCheckout}
                  disabled={isProcessing}
                >
                  {isProcessing ? 'Processing...' : 'Proceed to Checkout'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default CartModal;