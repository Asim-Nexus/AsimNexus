// ASIMNEXUS Browser Extension - Popup Script
// =========================================

document.addEventListener('DOMContentLoaded', function() {
  const chat = document.getElementById('chat');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const summarizeBtn = document.getElementById('summarize');
  const explainBtn = document.getElementById('explain');
  const writeBtn = document.getElementById('write');
  
  // Send message
  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    userInput.value = '';
    
    // Show typing indicator
    const typingId = showTyping();
    
    // Call ASIM API
    try {
      const response = await callASIMAPI(message);
      removeTyping(typingId);
      addMessage(response, 'asim');
    } catch (error) {
      removeTyping(typingId);
      addMessage('Sorry, I encountered an error. Please try again.', 'asim');
    }
  }
  
  function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }
  
  function showTyping() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message asim';
    div.innerHTML = 'Thinking<span class="dots">...</span>';
    div.style.fontStyle = 'italic';
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return id;
  }
  
  function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }
  
  async function callASIMAPI(message) {
    // Check if local ASIM is available
    const useLocal = await checkLocalASIM();
    
    if (useLocal) {
      // Call local ASIM instance
      return await callLocalASIM(message);
    } else {
      // Call cloud API
      return await callCloudAPI(message);
    }
  }
  
  async function checkLocalASIM() {
    try {
      const response = await fetch('http://localhost:8766/health', {
        method: 'GET',
        timeout: 1000
      });
      return response.ok;
    } catch {
      return false;
    }
  }
  
  async function callLocalASIM(message) {
    const response = await fetch('http://localhost:8766/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    
    const data = await response.json();
    return data.response || 'No response';
  }
  
  async function callCloudAPI(message) {
    // Call ASIM Cloud API
    const response = await fetch('https://api.asim-nexus.ai/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + await getAuthToken()
      },
      body: JSON.stringify({
        message,
        task_type: 'general',
        user_id: await getUserId()
      })
    });
    
    const data = await response.json();
    return data.response || 'No response';
  }
  
  // Get stored auth token
  async function getAuthToken() {
    const result = await chrome.storage.local.get(['authToken']);
    return result.authToken || '';
  }
  
  // Get user ID
  async function getUserId() {
    const result = await chrome.storage.local.get(['userId']);
    return result.userId || 'anonymous';
  }
  
  // Quick actions
  async function getPageContent() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        // Get main content
        const article = document.querySelector('article') || 
                       document.querySelector('main') ||
                       document.querySelector('.content') ||
                       document.body;
        return {
          title: document.title,
          content: article.innerText.substring(0, 5000), // First 5000 chars
          url: window.location.href
        };
      }
    });
    return results[0].result;
  }
  
  summarizeBtn.addEventListener('click', async () => {
    const page = await getPageContent();
    userInput.value = `Summarize this page: ${page.title}`;
    
    // Add context about the page
    const message = `Please summarize this webpage:\n\nTitle: ${page.title}\nURL: ${page.url}\n\nContent:\n${page.content}`;
    
    addMessage(`Summarize: ${page.title}`, 'user');
    const typingId = showTyping();
    
    try {
      const response = await callASIMAPI(message);
      removeTyping(typingId);
      addMessage(response, 'asim');
    } catch (error) {
      removeTyping(typingId);
      addMessage('Failed to summarize. Please try again.', 'asim');
    }
  });
  
  explainBtn.addEventListener('click', async () => {
    const page = await getPageContent();
    userInput.value = 'Explain this page simply';
    
    const message = `Explain this webpage in simple terms:\n\nTitle: ${page.title}\n\nContent:\n${page.content}`;
    
    addMessage('Explain this page', 'user');
    const typingId = showTyping();
    
    try {
      const response = await callASIMAPI(message);
      removeTyping(typingId);
      addMessage(response, 'asim');
    } catch (error) {
      removeTyping(typingId);
      addMessage('Failed to explain. Please try again.', 'asim');
    }
  });
  
  writeBtn.addEventListener('click', () => {
    userInput.value = 'Help me write ';
    userInput.focus();
  });
  
  // Event listeners
  sendBtn.addEventListener('click', sendMessage);
  
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });
  
  // Focus input
  userInput.focus();
});
