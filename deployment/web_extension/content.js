/* ASIMNEXUS Content Script - Injected into all web pages */

// Create ASIM floating button
function createASIMButton() {
  const button = document.createElement('div');
  button.id = 'asim-floating-button';
  button.innerHTML = '🧠';
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    z-index: 999999;
    transition: transform 0.3s, box-shadow 0.3s;
  `;
  
  button.addEventListener('mouseenter', () => {
    button.style.transform = 'scale(1.1)';
    button.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
  });
  
  button.addEventListener('mouseleave', () => {
    button.style.transform = 'scale(1)';
    button.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
  });
  
  button.addEventListener('click', () => {
    // Open side panel
    chrome.runtime.sendMessage({ action: 'openSidePanel' });
  });
  
  document.body.appendChild(button);
}

// Highlight text when selected
let selectedText = '';

document.addEventListener('selectionchange', () => {
  const selection = window.getSelection();
  selectedText = selection.toString().trim();
});

// Keyboard shortcuts
let lastKeyTime = 0;
document.addEventListener('keydown', (e) => {
  // Double-tap Ctrl to activate ASIM
  if (e.key === 'Control') {
    const now = Date.now();
    if (now - lastKeyTime < 300) {
      // Double tap detected
      if (selectedText) {
        // Send selected text to ASIM
        chrome.runtime.sendMessage({
          action: 'callASIM',
          prompt: selectedText,
          context: 'selection'
        });
      }
    }
    lastKeyTime = now;
  }
});

// Create ASIM tooltip for selected text
function createTooltip(x, y, text) {
  const existing = document.getElementById('asim-tooltip');
  if (existing) existing.remove();
  
  const tooltip = document.createElement('div');
  tooltip.id = 'asim-tooltip';
  tooltip.style.cssText = `
    position: absolute;
    left: ${x}px;
    top: ${y - 40}px;
    background: #333;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    z-index: 999999;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  `;
  tooltip.innerHTML = `
    <span style="cursor: pointer; margin-right: 10px;" onclick="window.postMessage({type: 'ASIM_SUMMARIZE', text: '${text.replace(/'/g, "\\'")}'}, '*')">📄 Summarize</span>
    <span style="cursor: pointer; margin-right: 10px;" onclick="window.postMessage({type: 'ASIM_EXPLAIN', text: '${text.replace(/'/g, "\\'")}'}, '*')">💡 Explain</span>
    <span style="cursor: pointer;" onclick="window.postMessage({type: 'ASIM_TRANSLATE', text: '${text.replace(/'/g, "\\'")}'}, '*')">🌐 Translate</span>
  `;
  
  document.body.appendChild(tooltip);
  
  // Remove after 5 seconds
  setTimeout(() => tooltip.remove(), 5000);
}

// Listen for mouse up to show tooltip
document.addEventListener('mouseup', (e) => {
  const selection = window.getSelection();
  const text = selection.toString().trim();
  
  if (text.length > 10) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    createTooltip(rect.left + rect.width / 2, rect.top, text);
  }
});

// Listen for messages from page
window.addEventListener('message', (event) => {
  if (event.data.type && event.data.type.startsWith('ASIM_')) {
    const action = event.data.type.replace('ASIM_', '').toLowerCase();
    
    chrome.runtime.sendMessage({
      action: 'callASIM',
      prompt: event.data.text,
      context: action
    }, (response) => {
      // Show result in a modal
      showResultModal(response.response);
    });
  }
});

// Show result modal
function showResultModal(content) {
  const modal = document.createElement('div');
  modal.id = 'asim-result-modal';
  modal.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 500px;
    max-height: 80vh;
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    z-index: 1000000;
    padding: 20px;
    overflow-y: auto;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  `;
  
  modal.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
      <h3 style="margin: 0; color: #333;">🧠 ASIM Response</h3>
      <button id="asim-close-modal" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
    </div>
    <div style="color: #555; line-height: 1.6; white-space: pre-wrap;">${content}</div>
    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
      <button id="asim-copy-btn" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-right: 10px;">📋 Copy</button>
      <button id="asim-chat-btn" style="background: #f3f4f6; color: #333; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">💬 Open Chat</button>
    </div>
  `;
  
  // Backdrop
  const backdrop = document.createElement('div');
  backdrop.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    z-index: 999999;
  `;
  
  document.body.appendChild(backdrop);
  document.body.appendChild(modal);
  
  // Event listeners
  document.getElementById('asim-close-modal').addEventListener('click', () => {
    modal.remove();
    backdrop.remove();
  });
  
  document.getElementById('asim-copy-btn').addEventListener('click', () => {
    navigator.clipboard.writeText(content);
    document.getElementById('asim-copy-btn').textContent = '✅ Copied!';
    setTimeout(() => {
      document.getElementById('asim-copy-btn').textContent = '📋 Copy';
    }, 2000);
  });
  
  document.getElementById('asim-chat-btn').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'openSidePanel' });
    modal.remove();
    backdrop.remove();
  });
  
  backdrop.addEventListener('click', () => {
    modal.remove();
    backdrop.remove();
  });
}

// Inject styles
const style = document.createElement('style');
style.textContent = `
  #asim-floating-button:hover::after {
    content: 'ASIM';
    position: absolute;
    right: 60px;
    background: #333;
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
  }
`;
document.head.appendChild(style);

// Initialize
createASIMButton();

console.log('🧠 ASIMNEXUS Content Script loaded');
