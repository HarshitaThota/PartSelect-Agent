
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getAIMessage = async (userQuery) => {
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: userQuery,
        conversation_history: []
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return {
      role: "assistant",
      content: data.message,
      parts: data.parts || [],
      query_type: data.query_type,
      confidence: data.confidence
    };
  } catch (error) {
    console.error('Error calling backend API:', error);
    return {
      role: "assistant",
      content: "Sorry, I'm having trouble connecting to the backend service. Please make sure the backend is running on port 8000."
    };
  }
};
