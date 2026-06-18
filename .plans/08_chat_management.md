# AsimNexus Nepal Ecosystem — Chat-Based Ecosystem Management

## Chat Management — "सबै काम Chat बाटै"

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    UNIVERSAL CHAT — ECOSYSTEM MANAGEMENT                                        │
│                    "AI सँग कुरा गरेर, आफ्नै Ecosystem व्यवस्थापन"                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Chat Commands (के-के गर्न सकिन्छ?)

| Command (नेपाली/English) | Action | Description |
|--------------------------|--------|-------------|
| "Ecosystem बनाउनुस्" / "Create ecosystem" | create | नयाँ Ecosystem सिर्जना |
| "File थप्नुस्" / "Add file" | add_file | नयाँ File सिर्जना |
| "Folder थप्नुस्" / "Add folder" | add_folder | नयाँ Folder सिर्जना |
| "Code थप्नुस्" / "Add code" | add_code | नयाँ Code लेख्ने |
| "Feature हटाउनुस्" / "Delete feature" | delete | Feature हटाउने |
| "Ecosystem अपडेट" / "Update ecosystem" | update | Ecosystem अपडेट |
| "Ecosystem मर्ज" / "Merge ecosystems" | merge | दुई Ecosystem मर्ज |
| "Ecosystem स्प्लिट" / "Split ecosystem" | split | Ecosystem विभाजन |

## Frontend Chat UI

```jsx
// frontend/react/src/components/chat/EcosystemChat.jsx

const EcosystemChat = ({ user }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    
    const handleSend = async () => {
        // 1. Send to AI
        // 2. AI Actions Execute
        // 3. Display Results
    };
    
    return (
        <div className="ecosystem-chat">
            <div className="ecosystem-selector">
                <button>👤 Personal</button>
                <button>🏢 Company</button>
                <button>🏛️ Government</button>
            </div>
            <div className="messages">
                {messages.map(msg => (
                    <div className={`message ${msg.role}`}>
                        {msg.content}
                        {msg.actions && (
                            <div className="actions">
                                {msg.actions.map(action => (
                                    <button onClick={() => handleAction(action)}>
                                        {action.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
            <input 
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="AsimNexus लाई के गर्नुहुन्छ?"
            />
        </div>
    );
};
```

## Backend Chat Route

```python
# backend/chat_routes.py

@chat_router.post("/ecosystem")
async def ecosystem_chat(request: EcosystemChatRequest):
    """
    Chat बाटै Ecosystem Management
    - Intent पार्स गर्छ
    - Permission Check गर्छ
    - Action Execute गर्छ
    - Dharma Veto Check गर्छ
    """
    intent = await intent_parser.parse(request.message)
    allowed = await permission.check(user_role, intent.action, intent.ecosystem_type)
    
    if intent.action == "create":
        result = await _create_ecosystem(intent)
    elif intent.action == "add_file":
        result = await _add_file(intent)
    # ... other actions
    
    dharma_result = await dharma.check(result)
    return result
```

## Intent Parser

| Message | Intent | Ecosystem Type |
|---------|--------|---------------|
| "मेरो कम्पनीको Ecosystem बनाउनुस्" | create | company |
| "नयाँ Health Connector थप्नुस्" | add_file | health |
| "Education Ecosystem अपडेट" | update | education |
| "Government + Company मर्ज" | merge | hybrid |