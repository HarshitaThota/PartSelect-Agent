import React from 'react';
import './PartCard.css';

function PartCard({ part, onAddToCart, onViewDetails, isInCart = false }) {
  const handleAddToCart = () => {
    if (onAddToCart && !isInCart) {
      onAddToCart(part);
    }
  };

  const handleViewDetails = () => {
    if (onViewDetails) {
      onViewDetails(part);
    }
  };

  return (
    <div className="part-card">
      <div className="part-header">
        <h4 className="part-name">{part.name}</h4>
        <span className="part-number">#{part.partselect_number}</span>
      </div>

      <div className="part-info">
        <div className="brand-appliance">
          <span className="brand">{part.brand}</span>
          <span className="appliance-type">{part.appliance_type}</span>
        </div>

        <div className="price-stock">
          <span className="price">${part.price}</span>
          <span className={`stock-status ${part.in_stock ? 'in-stock' : 'out-stock'}`}>
            {part.in_stock ? 'In Stock' : 'Out of Stock'}
          </span>
        </div>

        {part.description && (
          <p className="part-description">{part.description}</p>
        )}

        {part.installation_difficulty && (
          <div className="installation-info">
            <span className="difficulty">
              Difficulty: {part.installation_difficulty}
            </span>
          </div>
        )}
      </div>

      <div className="part-actions">
        <button
          className={`add-to-cart-btn ${isInCart ? 'in-cart' : ''}`}
          onClick={handleAddToCart}
          disabled={!part.in_stock || isInCart}
        >
          {isInCart ? 'In Cart' : part.in_stock ? 'Add to Cart' : 'Out of Stock'}
        </button>

        <button
          className="view-details-btn"
          onClick={handleViewDetails}
        >
          View Details
        </button>
      </div>
    </div>
  );
}

export default PartCard;