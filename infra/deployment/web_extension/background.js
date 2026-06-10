// ASIMNEXUS Browser Extension - Background Service Worker
// ========================================================

// Extension state
const state = {
  isInitialized: false,
  userId: null,
  authToken: null,
  lastActiveTab: null,
  asimStatus: 'disconnected'
};

// Initialize extension
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('🧠 ASIMNEXUS Extension installed');
  
  // Set default settings
  await chrome.storage.local.set({
    'asimServerUrl': 'http://localhost:8766',
    'cloudApiUrl': 'https://api.asim-nexus.ai',
    'useLocal': true,
    'notifications': true,
    'shortcutsEnabled': true
  });
  
  // Check ASIM connection
  await checkASIMConnection();
  
  // Create context menu items
  createContextMenus();
});

// Check ASIM server connection
async function checkASIMConnection() {
  try {
    const settings = await chrome.storage.local.get(['asimServerUrl']);
    const response = await fetch(`${settings.asimServerUrl}/health`, {
      method: 'GET',
      timeout: 2000
    });
    
    if (response.ok) {
      state.asimStatus = 'connected';
      updateBadge('✓', '#4ade80');
    } else {
      state.asimStatus = 'cloud';
      updateBadge('☁', '#60a5fa');
    }
  } catch (error) {
    state.asimStatus = 'cloud';
    updateBadge('☁', '#60a5fa');
  }
}

// Update extension badge
function updateBadge(text, color) {
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color });
}

// Create context menu items
function createContextMenus() {
  chrome.contextMenus.create({
    id: 'asim-summarize',
    title: '📄 Summarize with ASIM',
    contexts: ['page', 'selection']
  });
  
  chrome.contextMenus.create({
    id: 'asim-explain',
    title: '💡 Explain with ASIM',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'asim-write',
    title: '✍️ Help me write',
    contexts: ['editable']
  });
  
  chrome.contextMenus.create({
    id: 'asim-translate',
    title: '🌐 Translate with ASIM',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'asim-code',
    title: '💻 Code help',
    contexts: ['selection']
  });
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const selectedText = info.selectionText || '';
  const pageUrl = tab.url;
  
  switch (info.menuItemId) {
    case 'asim-summarize':
      await handleSummarize(tab, selectedText, pageUrl);
      break;
    
    case 'asim-explain':
      await handleExplain(tab, selectedText);
      break;
    
    case 'asim-write':
      await handleWrite(tab, selectedText);
      break;
    
    case 'asim-translate':
      await handleTranslate(tab, selectedText);
      break;
    
    case 'asim-code':
      await handleCodeHelp(tab, selectedText);
      break;
  }
});

// Summarize handler
async function handleSummarize(tab, selectedText, pageUrl) {
  // Open side panel
  await chrome.sidePanel.open({ windowId: tab.windowId });
  
  // Get page content
  const pageContent = await getPageContent(tab.id);
  
  // Send to ASIM
  const prompt = selectedText 
    ? `Summarize this text:\n${selectedText}`
    : `Summarize this page:\nTitle: ${pageContent.title}\n\nContent:\n${pageContent.content}`;
  
  // Send message to side panel
  setTimeout(() => {
    chrome.runtime.sendMessage({
      action: 'sendToASIM',
      prompt: prompt,
      context: 'summarize'
    });
  }, 500);
}

// Explain handler
async function handleExplain(tab, selectedText) {
  await chrome.sidePanel.open({ windowId: tab.windowId });
  
  const prompt = `Explain this in simple terms:\n${selectedText}`;
  
  setTimeout(() => {
    chrome.runtime.sendMessage({
      action: 'sendToASIM',
      prompt: prompt,
      context: 'explain'
    });
  }, 500);
}

// Write handler
async function handleWrite(tab, selectedText) {
  await chrome.sidePanel.open({ windowId: tab.windowId });
  
  const prompt = `Help me write about:\n${selectedText}\n\nPlease provide suggestions and improvements.`;
  
  setTimeout(() => {
    chrome.runtime.sendMessage({
      action: 'sendToASIM',
      prompt: prompt,
      context: 'write'
    });
  }, 500);
}

// Translate handler
async function handleTranslate(tab, selectedText) {
  await chrome.sidePanel.open({ windowId: tab.windowId });
  
  const prompt = `Translate this to English (if not English) or to Nepali (if English):\n${selectedText}`;
  
  setTimeout(() => {
    chrome.runtime.sendMessage({
      action: 'sendToASIM',
      prompt: prompt,
      context: 'translate'
    });
  }, 500);
}

// Code help handler
async function handleCodeHelp(tab, selectedText) {
  await chrome.sidePanel.open({ windowId: tab.windowId });
  
  const prompt = `Help with this code:\n\`\`\`\n${selectedText}\n\`\`\`\n\nExplain what it does and suggest improvements.`;
  
  setTimeout(() => {
    chrome.runtime.sendMessage({
      action: 'sendToASIM',
      prompt: prompt,
      context: 'code'
    });
  }, 500);
}

// Get page content from content script
async function getPageContent(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: () => {
        const article = document.querySelector('article') || 
                       document.querySelector('main') ||
                       document.querySelector('.content') ||
                       document.querySelector('[role="main"]') ||
                       document.body;
        
        return {
          title: document.title,
          content: article.innerText.substring(0, 8000),
          url: window.location.href
        };
      }
    });
    
    return results[0].result;
  } catch (error) {
    return {
      title: 'Unknown',
      content: '',
      url: ''
    };
  }
}

// Keyboard shortcuts
chrome.commands.onCommand.addListener(async (command) => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  switch (command) {
    case 'open_chat':
      // Open side panel
      await chrome.sidePanel.open({ windowId: tab.windowId });
      break;
    
    case 'summarize_page':
      await handleSummarize(tab, '', tab.url);
      break;
  }
});

// Tab change listener
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  state.lastActiveTab = activeInfo.tabId;
  
  // Check if we're on a supported page
  const tab = await chrome.tabs.get(activeInfo.tabId);
  
  if (tab.url && (tab.url.startsWith('http://') || tab.url.startsWith('https://'))) {
    // Enable actions
    chrome.action.enable();
  } else {
    // Disable on chrome:// pages
    chrome.action.disable();
  }
});

// Message handling
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'getPageContent':
      getPageContent(sender.tab.id).then(sendResponse);
      return true; // Async response
    
    case 'checkConnection':
      checkASIMConnection().then(() => {
        sendResponse({ status: state.asimStatus });
      });
      return true;
    
    case 'callASIM':
      callASIMAPI(request.prompt, request.context).then(sendResponse);
      return true;
  }
});

// Call ASIM API
async function callASIMAPI(prompt, context = 'general') {
  try {
    const settings = await chrome.storage.local.get([
      'asimServerUrl', 'cloudApiUrl', 'useLocal'
    ]);
    
    // Try local first if enabled
    if (settings.useLocal) {
      try {
        const response = await fetch(`${settings.asimServerUrl}/v1/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: prompt,
            task_type: context
          }),
          timeout: 30000
        });
        
        if (response.ok) {
          const data = await response.json();
          return { success: true, response: data.response, source: 'local' };
        }
      } catch (e) {
        // Fall through to cloud
      }
    }
    
    // Try cloud API
    const response = await fetch(`${settings.cloudApiUrl}/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        message: prompt,
        task_type: context
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return { success: true, response: data.response, source: 'cloud' };
    } else {
      return { success: false, error: 'API error' };
    }
    
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// Get auth token
async function getAuthToken() {
  const result = await chrome.storage.local.get(['authToken']);
  return result.authToken || '';
}

// Periodic connection check
setInterval(checkASIMConnection, 30000); // Every 30 seconds

console.log('🧠 ASIMNEXUS Background Service Worker initialized');
