# Frontend Integration Guide

This guide is intended for frontend developers who need to integrate with the AI Co-Pilot Mental Health Support backend.

## Overview

The backend provides a RESTful API that simulates conversations between a student seeking mental health support and an educator providing guidance. The frontend should:

1. Start a conversation
2. Display messages from both the student and educator
3. Show typing indicators
4. Display real-time feedback for the educator
5. Allow for conversation transcript retrieval

## API Access

### Base URL

Always use the CORS proxy URL to avoid cross-origin issues:

```javascript
const API_URL = 'http://127.0.0.1:5070';
```

If you're developing in a cloud environment (like Stackblitz, CodeSandbox), you'll need the backend exposed via ngrok or similar service.

## Key Endpoints

### 1. Start Conversation

```javascript
async function startConversation(turns = 5) {
  const response = await fetch(`${API_URL}/api/conversations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ turns })
  });
  
  return response.json();
}

// Example usage:
const { conversation_id } = await startConversation();
```

### 2. Get Conversation Events (Long Polling)

This endpoint uses long polling to provide real-time updates. It waits for new events and returns them as they occur.

```javascript
async function getEvents(conversationId, lastIndex = 0) {
  const response = await fetch(
    `${API_URL}/api/conversations/${conversationId}/events?last_index=${lastIndex}`
  );
  
  return response.json();
}

// Recursive polling function:
async function pollEvents(conversationId, lastIndex = 0, onEvent) {
  try {
    const data = await getEvents(conversationId, lastIndex);
    
    if (data.events && data.events.length > 0) {
      // Process events
      data.events.forEach(event => onEvent(event));
      
      // Continue polling with updated index
      pollEvents(conversationId, data.last_index, onEvent);
    } else {
      // No new events, poll again after a delay
      setTimeout(() => pollEvents(conversationId, lastIndex, onEvent), 1000);
    }
  } catch (error) {
    console.error("Error polling events:", error);
    // Retry after a longer delay
    setTimeout(() => pollEvents(conversationId, lastIndex, onEvent), 3000);
  }
}
```

### 3. End Conversation

```javascript
async function endConversation(conversationId) {
  const response = await fetch(`${API_URL}/api/conversations/${conversationId}`, {
    method: 'DELETE'
  });
  
  return response.json();
}
```

### 4. Get Conversation Transcript

```javascript
async function getTranscript(conversationId) {
  const response = await fetch(
    `${API_URL}/api/conversations/${conversationId}/transcript`
  );
  
  return response.json();
}
```

## Event Types

The backend emits three types of events:

### 1. Message Events

```json
{
  "type": "message",
  "speaker": "student", // or "educator"
  "name": "Alex", // or "Ms. Morgan"
  "text": "Hi Ms. Morgan, I've been feeling really overwhelmed lately...",
  "timestamp": "2023-05-05T12:34:59.123"
}
```

### 2. Typing Indicators

```json
{
  "type": "typing",
  "speaker": "educator", // or "student"
  "name": "Ms. Morgan", // or "Alex"
  "timestamp": "2023-05-05T12:34:56.789"
}
```

### 3. Feedback Events

```json
{
  "type": "feedback",
  "feedback": {
    "analysis": "The student is expressing feelings of anxiety related to academic pressure.",
    "suggestions": [
      "Validate their feelings",
      "Explore specific stressors",
      "Consider suggesting stress management techniques"
    ]
  },
  "timestamp": "2023-05-05T12:35:00.456"
}
```

## Complete Example

Here's a simple example of how to use the API:

```javascript
// Start conversation
const { conversation_id } = await startConversation();

// Process events
function handleEvent(event) {
  switch(event.type) {
    case 'message':
      console.log(`${event.name}: ${event.text}`);
      // Add message to UI
      break;
      
    case 'typing':
      console.log(`${event.name} is typing...`);
      // Show typing indicator in UI
      break;
      
    case 'feedback':
      console.log('Feedback:', event.feedback.analysis);
      console.log('Suggestions:', event.feedback.suggestions);
      // Show feedback in UI for educator
      break;
  }
}

// Start polling for events
pollEvents(conversation_id, 0, handleEvent);

// Later, end the conversation
const result = await endConversation(conversation_id);
console.log('Conversation ended:', result);
```

## Common Issues

### 1. CORS Errors

If you see "Failed to fetch" errors in the console, make sure:
- The backend and CORS proxy are running (`python main.py`)
- You're using the correct proxy URL (`http://127.0.0.1:5070`)
- Your browser allows cross-origin requests (not an issue if using the proxy)

### 2. Connection Issues in Cloud Environments

If developing in a cloud-based IDE or environment:
1. The backend server needs to be accessible over the public internet
2. Use a service like ngrok:
   ```
   ngrok http 5070
   ```
3. Update your base URL to the ngrok URL:
   ```javascript
   const API_URL = 'https://your-unique-id.ngrok.io';
   ```

### 3. Long-Polling Timeouts

The long-polling endpoint has a 30-second timeout. If your frontend receives empty responses regularly, this is normal. Just continue polling as shown in the examples.

## Need Help?

If you're experiencing issues integrating with the backend, try:

1. Use the test tools in `debug_tools/` to verify the server is working
2. Check browser console for detailed error messages
3. Refer to the API documentation in the main README 