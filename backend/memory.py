#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade memory backend
ASIMNEXUS Memory Backend
========================
Memory API endpoints for vector memory operations.
Provides REST interface to core.vectormemory.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("AsimNexus.Memory")


def setup_memory_routes(app, db_path: str = "data/vector_memory.db"):
    """
    Setup memory API routes on FastAPI app.
    Call this from simple_backend.py to wire memory endpoints.
    """
    from core.vectormemory import get_vector_memory, MemoryType, EmbeddingBackend
    
    # Initialize vector memory
    vector_memory = get_vector_memory(db_path, EmbeddingBackend.DUMMY)
    
    class AddMemoryRequest(BaseModel):
        """Request model for adding memory."""
        content: str
        memory_type: str = "chat"
        user_id: str = "anonymous"
        metadata: Optional[Dict[str, Any]] = None
    
    class SearchRequest(BaseModel):
        """Request model for searching memory."""
        query: str
        user_id: Optional[str] = None
        memory_type: Optional[str] = None
        limit: int = 10
        min_similarity: float = 0.5
    
    @app.post("/api/memory/add")
    async def add_memory(req: AddMemoryRequest):
        """Add a memory to the vector store."""
        try:
            # Convert string to enum
            try:
                memory_type = MemoryType(req.memory_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid memory_type: {req.memory_type}")
            
            memory_id = vector_memory.add_memory(
                content=req.content,
                memory_type=memory_type,
                user_id=req.user_id,
                metadata=req.metadata
            )
            
            return JSONResponse({
                "id": memory_id,
                "content": req.content,
                "memory_type": req.memory_type,
                "user_id": req.user_id
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Add memory error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/memory/{memory_id}")
    async def get_memory(memory_id: str):
        """Get a memory by ID."""
        try:
            memory = vector_memory.get_memory(memory_id)
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return JSONResponse({
                "id": memory.id,
                "content": memory.content,
                "memory_type": memory.memory_type.value,
                "user_id": memory.user_id,
                "metadata": memory.metadata,
                "created_at": memory.created_at,
                "access_count": memory.access_count,
                "last_accessed": memory.last_accessed
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get memory error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/memory/search")
    async def search_memory(req: SearchRequest):
        """Search memories by semantic similarity."""
        try:
            # Convert string to enum if provided
            memory_type = None
            if req.memory_type:
                try:
                    memory_type = MemoryType(req.memory_type)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid memory_type: {req.memory_type}")
            
            results = vector_memory.search(
                query=req.query,
                user_id=req.user_id,
                memory_type=memory_type,
                limit=req.limit,
                min_similarity=req.min_similarity
            )
            
            return JSONResponse([
                {
                    "memory": {
                        "id": r.memory.id,
                        "content": r.memory.content,
                        "memory_type": r.memory.memory_type.value,
                        "user_id": r.memory.user_id,
                        "created_at": r.memory.created_at
                    },
                    "similarity": r.similarity,
                    "distance": r.distance
                }
                for r in results
            ])
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Search memory error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/memory/user/{user_id}")
    async def get_user_memories(user_id: str, memory_type: Optional[str] = None, limit: int = 50):
        """Get all memories for a user."""
        try:
            # Convert string to enum if provided
            mt = None
            if memory_type:
                try:
                    mt = MemoryType(memory_type)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid memory_type: {memory_type}")
            
            memories = vector_memory.get_user_memories(user_id, mt, limit)
            
            return JSONResponse([
                {
                    "id": m.id,
                    "content": m.content,
                    "memory_type": m.memory_type.value,
                    "user_id": m.user_id,
                    "metadata": m.metadata,
                    "created_at": m.created_at,
                    "access_count": m.access_count
                }
                for m in memories
            ])
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user memories error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/api/memory/recent")
    async def recent_memories(user_id: str = "anonymous", limit: int = 20):
        """Get recent memories for user."""
        try:
            from core.vectormemory import get_vector_memory, EmbeddingBackend
            vm = get_vector_memory(db_path, EmbeddingBackend.DUMMY)
            memories = vm.get_user_memories(user_id, limit=limit)
            return JSONResponse([{
                "id": m.id,
                "content": m.content,
                "memory_type": m.memory_type.value,
                "user_id": m.user_id,
                "created_at": m.created_at
            } for m in memories])
        except Exception as e:
            logger.error(f"Recent memories error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @app.delete("/api/memory/{memory_id}")
    async def delete_memory(memory_id: str):
        """Delete a memory by ID."""
        try:
            success = vector_memory.delete_memory(memory_id)
            if not success:
                raise HTTPException(status_code=404, detail="Memory not found")
            return JSONResponse({"deleted": True})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete memory error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
     
    @app.get("/api/memory/stats")
    async def get_memory_stats():
        """Get memory statistics."""
        try:
            stats = vector_memory.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get memory stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/memory/prune")
    async def prune_memories(days: int = 90, keep_per_type: int = 100):
        """Prune old memories."""
        try:
            deleted = vector_memory.prune_old_memories(days, keep_per_type)
            return JSONResponse({
                "deleted": deleted,
                "days": days,
                "keep_per_type": keep_per_type
            })
        except Exception as e:
            logger.error(f"Prune memories error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
