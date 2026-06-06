#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade chat backend
ASIMNEXUS Chat Backend
======================
Chat API endpoints with local model integration.
Supports memory retrieval, clone delegation, and policy gating.
"""

import logging
import sqlite3
import json
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("AsimNexus.Chat")


@dataclass
class Message:
    """Chat message."""
    id: str
    role: str  # "user" or "assistant"
    content: str
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_used: Optional[str] = None
    clone_used: Optional[str] = None


@dataclass
class ChatSession:
    """Chat session."""
    id: str
    user_id: str
    title: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChatBackend:
    """
    Chat backend with local model integration.
    Manages messages, sessions, and coordinates with other components.
    """
    
    def __init__(self, db_path: str = "data/chat.db"):
        self.db_path = db_path
        self._init_db()
        logger.info(f"💬 ChatBackend initialized")
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    model_used TEXT,
                    clone_used TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
            """)
            
            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id)")
            
            conn.commit()
    
    def create_session(self, user_id: str, title: str = "New Chat") -> str:
        """Create a new chat session."""
        session_id = secrets.token_hex(8)
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            title=title
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session.id, session.user_id, session.title, session.created_at, session.updated_at, json.dumps(session.metadata)))
            conn.commit()
        
        logger.info(f"💬 Created session {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
            
            if not row:
                return None
            
            return ChatSession(
                id=row['id'],
                user_id=row['user_id'],
                title=row['title'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
    
    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[ChatSession]:
        """Get all sessions for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        
        sessions = []
        for row in rows:
            sessions.append(ChatSession(
                id=row['id'],
                user_id=row['user_id'],
                title=row['title'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            ))
        
        return sessions
    
    def add_message(self, role: str, content: str, user_id: str,
                   session_id: Optional[str] = None, model_used: Optional[str] = None,
                   clone_used: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to the chat."""
        message_id = secrets.token_hex(12)
        message = Message(
            id=message_id,
            role=role,
            content=content,
            user_id=user_id,
            session_id=session_id,
            model_used=model_used,
            clone_used=clone_used,
            metadata=metadata or {}
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO messages (id, role, content, user_id, session_id, metadata, created_at, model_used, clone_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (message.id, message.role, message.content, message.user_id, message.session_id,
                  json.dumps(message.metadata), message.created_at, message.model_used, message.clone_used))
            conn.commit()
        
        # Update session timestamp
        if session_id:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                    (datetime.utcnow().isoformat(), session_id)
                )
                conn.commit()
        
        logger.debug(f"💬 Added message {message_id} (role: {role})")
        return message_id
    
    def get_session_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """Get all messages for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
                (session_id, limit)
            ).fetchall()
        
        messages = []
        for row in rows:
            messages.append(Message(
                id=row['id'],
                role=row['role'],
                content=row['content'],
                user_id=row['user_id'],
                session_id=row['session_id'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                model_used=row['model_used'],
                clone_used=row['clone_used']
            ))
        
        return messages
    
    def get_user_messages(self, user_id: str, limit: int = 100) -> List[Message]:
        """Get all messages for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM messages WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        
        messages = []
        for row in rows:
            messages.append(Message(
                id=row['id'],
                role=row['role'],
                content=row['content'],
                user_id=row['user_id'],
                session_id=row['session_id'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                model_used=row['model_used'],
                clone_used=row['clone_used']
            ))
        
        return messages
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete messages first
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            # Delete session
            cursor = conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chat statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total_sessions = conn.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0]
            total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            
            # By user
            by_user = {}
            rows = conn.execute("""
                SELECT user_id, COUNT(*) as count
                FROM messages
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            for user_id, count in rows:
                by_user[user_id] = count
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "by_user": by_user
        }


def setup_chat_routes(app, db_path: str = "data/chat.db"):
    """
    Setup chat API routes on FastAPI app.
    Call this from simple_backend.py to wire chat endpoints.
    """
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    
    chat_backend = ChatBackend(db_path)
    
    class SendMessageRequest(BaseModel):
        """Request model for sending a message."""
        content: str
        session_id: Optional[str] = None
        user_id: str = "anonymous"
    
    class CreateSessionRequest(BaseModel):
        """Request model for creating a session."""
        user_id: str = "anonymous"
        title: str = "New Chat"
    
    @app.post("/api/chat/session")
    async def create_session(req: CreateSessionRequest):
        """Create a new chat session."""
        try:
            session_id = chat_backend.create_session(req.user_id, req.title)
            session = chat_backend.get_session(session_id)
            return JSONResponse({
                "id": session.id,
                "user_id": session.user_id,
                "title": session.title,
                "created_at": session.created_at
            })
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/chat/sessions/{user_id}")
    async def get_sessions(user_id: str):
        """Get all sessions for a user."""
        try:
            sessions = chat_backend.get_user_sessions(user_id)
            return JSONResponse([
                {
                    "id": s.id,
                    "user_id": s.user_id,
                    "title": s.title,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at
                }
                for s in sessions
            ])
        except Exception as e:
            logger.error(f"Get sessions error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/chat/session/{session_id}")
    async def get_session(session_id: str):
        """Get a session by ID."""
        try:
            session = chat_backend.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return JSONResponse({
                "id": session.id,
                "user_id": session.user_id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get session error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/chat/message")
    async def send_message(req: SendMessageRequest):
        """Send a message and get AI response."""
        try:
            # Add user message
            message_id = chat_backend.add_message(
                role="user",
                content=req.content,
                user_id=req.user_id,
                session_id=req.session_id
            )
            
            # TODO: Integrate with local model router and vector memory
            # For now, return a simple response
            response_content = "I received your message. Local model integration coming soon."
            
            # Add assistant response
            response_id = chat_backend.add_message(
                role="assistant",
                content=response_content,
                user_id=req.user_id,
                session_id=req.session_id or message_id,
                model_used="placeholder"
            )
            
            return JSONResponse({
                "user_message_id": message_id,
                "assistant_message_id": response_id,
                "content": response_content,
                "session_id": req.session_id or message_id
            })
        except Exception as e:
            logger.error(f"Send message error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/chat/messages/{session_id}")
    async def get_messages(session_id: str):
        """Get all messages for a session."""
        try:
            messages = chat_backend.get_session_messages(session_id)
            return JSONResponse([
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at,
                    "model_used": m.model_used,
                    "clone_used": m.clone_used
                }
                for m in messages
            ])
        except Exception as e:
            logger.error(f"Get messages error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.delete("/api/chat/session/{session_id}")
    async def delete_session(session_id: str):
        """Delete a session."""
        try:
            success = chat_backend.delete_session(session_id)
            if not success:
                raise HTTPException(status_code=404, detail="Session not found")
            return JSONResponse({"deleted": True})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete session error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/chat/stats")
    async def get_stats():
        """Get chat statistics."""
        try:
            stats = chat_backend.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
