# ASIMNEXUS Frontend Architecture Documentation

## Overview

ASIMNEXUS frontend is built following 2026 enterprise best practices from Netflix, Shopify, and Vercel. The architecture focuses on modularity, performance, type safety, and maintainability.

## Architecture Principles

### 1. Modular Component Architecture (Lego-Brick Style)

Components are designed as small, reusable, independent building blocks that can be composed together to build complex UIs.

**Benefits:**
- Easy to test and maintain
- Reusable across the application
- Clear separation of concerns
- Faster development with pre-built components

**Structure:**
```
src/
├── components/
│   ├── chat/              # Chat-specific modular components
│   │   ├── ChatHeader.js
│   │   ├── ChatMessage.js
│   │   ├── ChatInput.js
│   │   ├── FounderSelector.js
│   │   ├── QuickReplies.js
│   │   └── ChatSuggestions.js
│   ├── Dashboard.js
│   └── FounderPanel.js
├── design-system/         # Reusable UI library
│   ├── components/
│   │   ├── Button.js
│   │   ├── Input.js
│   │   └── Card.js
│   └── tokens/
│       └── index.js
└── hooks/                 # Custom React hooks
    ├── useChatState.js
    ├── useStreamingChat.js
    └── useRealTimeMetrics.js
```

### 2. Design System

A centralized design system ensures consistency across the application.

**Design Tokens:**
- Colors: Primary, secondary, semantic (success, warning, error), neutral, dark mode
- Spacing: xs, sm, md, lg, xl, 2xl, 3xl, 4xl
- Typography: Font families, sizes, weights, line heights
- Border radius: sm, md, lg, xl, 2xl, full
- Shadows: sm, md, lg, xl, 2xl
- Transitions: fast, base, slow
- Z-index: dropdown, sticky, fixed, modal, tooltip
- Breakpoints: sm, md, lg, xl, 2xl

**Components:**
- Button: Primary, secondary, ghost, danger, success variants
- Input: With validation, icons, error states
- Card: Default, elevated, outlined, dark variants

### 3. State Management Strategy

Following the separation of Local UI State and Server State pattern.

**Local UI State:**
- Component-level ephemeral state
- UI interactions (modals, dropdowns, toggles)
- Form inputs
- Temporary selections

**Server State:**
- Data from backend APIs
- Cached and synchronized
- Managed via custom hooks
- Optimistic updates

**Implementation:**
```javascript
// useChatState.js - Manages all chat-related state
export const useChatState = () => {
  // Local UI State
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  
  // Server State
  const [messages, setMessages] = useState([]);
  const [filteredMessages, setFilteredMessages] = useState([]);
  
  // Actions
  const addReaction = useCallback((messageId, emoji) => { ... }, []);
  
  return { /* state and actions */ };
};
```

### 4. Performance as a Feature

**Memoization:**
- All modular components wrapped with `React.memo`
- Prevents unnecessary re-renders
- Improves performance for large message lists

**Code Splitting:**
- Components can be lazy-loaded using React.lazy
- Reduces initial bundle size
- Faster page load times

**Optimistic Updates:**
- UI updates immediately before server confirmation
- Better perceived performance
- Rollback on error

### 5. Advanced Chat UI Features

**Streaming:**
- Real-time streaming responses from backend
- `useStreamingChat` hook for managing streaming
- AbortController for cancellation
- Fallback to regular API if streaming unavailable

**Markdown Support:**
- ReactMarkdown for rendering markdown
- remark-gfm for GitHub Flavored Markdown
- Tables, lists, code blocks, links

**Code Highlighting:**
- react-syntax-highlighter for code blocks
- VS Code Dark Plus theme
- Language detection
- Copy code functionality

**Message Actions:**
- Reply, edit, delete, pin, copy, share
- Reactions with emoji picker
- Priority levels (normal, high, urgent)
- Message editing history

### 6. Real-Time Dashboard

**WebSocket Integration:**
- `useRealTimeMetrics` hook for WebSocket connection
- Real-time system metrics (CPU, memory, network, storage)
- Active founders and agents count
- Ethical score monitoring
- Fallback to simulated data if WebSocket unavailable

**Advanced Charts:**
- Area charts for activity over time
- Pie charts for task distribution
- Animated transitions
- Responsive design

**Design System Integration:**
- All metric cards use Card component
- Motion animations for value changes
- Consistent styling across dashboard

## Component Guidelines

### Creating New Components

1. **Keep it small:** Each component should have a single responsibility
2. **Use memo:** Wrap with `React.memo` for performance
3. **Design system first:** Use design system components when possible
4. **Props interface:** Document all props with JSDoc
5. **Styling:** Use design tokens instead of hardcoded values

Example:
```javascript
import React, { memo } from 'react';
import { Button } from '../../design-system/components';

const MyComponent = ({ title, onClick, variant = 'primary' }) => {
  return (
    <div className="my-component">
      <h3>{title}</h3>
      <Button variant={variant} onClick={onClick}>
        Action
      </Button>
    </div>
  );
};

export default memo(MyComponent);
```

### State Management Guidelines

1. **Local state:** Use for component-specific UI state
2. **Custom hooks:** Extract complex state logic into hooks
3. **Server state:** Use hooks that handle API calls and caching
4. **Context:** Use for global state (theme, user auth)

Example:
```javascript
// Create a custom hook for complex state
export const useMyFeature = () => {
  const [state, setState] = useState(initialState);
  
  const action = useCallback(() => {
    // Logic here
  }, [dependencies]);
  
  return { state, action };
};
```

## Performance Best Practices

1. **Memoization:**
   - Use `React.memo` for components
   - Use `useCallback` for functions passed to children
   - Use `useMemo` for expensive computations

2. **Code Splitting:**
   ```javascript
   const LazyComponent = React.lazy(() => import('./LazyComponent'));
   ```

3. **Lazy Loading:**
   - Load heavy libraries on demand
   - Use dynamic imports for non-critical features

4. **Bundle Optimization:**
   - Analyze bundle size regularly
   - Remove unused dependencies
   - Use tree-shaking

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Test state management hooks

### Integration Tests
- Test component interactions
- Test API integrations
- Test state flow

### E2E Tests
- Test user flows
- Test critical paths
- Use Playwright or Cypress

## Deployment

### Build Process
```bash
npm run build
```

### Environment Variables
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_WS_URL`: WebSocket URL
- `REACT_APP_ENVIRONMENT`: Environment (dev, staging, prod)

### Performance Monitoring
- Use React DevTools Profiler
- Monitor bundle size
- Track Core Web Vitals

## Future Enhancements

1. **TypeScript Migration:**
   - Add type definitions for all components
   - Improve type safety
   - Better developer experience

2. **Testing Infrastructure:**
   - Add Jest for unit tests
   - Add React Testing Library
   - Add Playwright for E2E tests

3. **Advanced Features:**
   - Virtual scrolling for large message lists
   - Offline support with service workers
   - PWA capabilities
   - Advanced analytics

## Conclusion

The ASIMNEXUS frontend architecture follows modern best practices to ensure:
- **Scalability:** Easy to add new features
- **Maintainability:** Clear structure and separation of concerns
- **Performance:** Optimized rendering and loading
- **Developer Experience:** Consistent patterns and tools
- **User Experience:** Fast, responsive, and beautiful UI

This architecture is future-proof and can evolve with the project's needs.
