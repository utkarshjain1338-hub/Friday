"""
Enhanced Memory Database with Multiple Memory Types
Supports Episodic, Semantic, and Procedural memory
"""

import sqlite3
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger


class EnhancedMemoryDatabase:
    """Multi-type memory storage system"""
    
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path or Path.cwd() / "friday_memory_enhanced.db")
        self.connection = sqlite3.connect(str(self.path), check_same_thread=False, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self._create_tables()
        logger.info(f"Memory database initialized at {self.path}")
    
    def _create_tables(self):
        """Create all memory tables"""
        with self.lock:
            cursor = self.connection.cursor()
            
            # Episodic Memory: Experiences and events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    description TEXT,
                    context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    importance REAL DEFAULT 0.5,
                    tags TEXT,
                    metadata TEXT
                )
            """)
            
            # Semantic Memory: Facts and knowledge
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id INTEGER PRIMARY KEY,
                    fact_type TEXT NOT NULL,
                    key TEXT UNIQUE,
                    value TEXT,
                    confidence REAL DEFAULT 1.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Procedural Memory: Workflows and procedures
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS procedural_memory (
                    id INTEGER PRIMARY KEY,
                    procedure_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    steps TEXT,
                    frequency TEXT,
                    last_executed DATETIME,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Relationship Graph: Entity relationships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY,
                    entity_a TEXT NOT NULL,
                    entity_b TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.5,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Legacy memory table (for backward compatibility)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            logger.info("Memory tables initialized")
    
    # ===== EPISODIC MEMORY =====
    
    def store_episode(
        self,
        event_name: str,
        description: str,
        context: Optional[str] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store an episodic memory (experience/event)
        
        Args:
            event_name: Name of the event
            description: Detailed description
            context: Context information
            importance: Importance score (0-1)
            tags: List of tags
            metadata: Additional metadata
            
        Returns:
            ID of stored episode
        """
        with self.lock:
            cursor = self.connection.cursor()
            tags_str = json.dumps(tags) if tags else None
            metadata_str = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO episodic_memory 
                (event_name, description, context, importance, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_name, description, context, importance, tags_str, metadata_str))
            
            self.connection.commit()
            episode_id = cursor.lastrowid
            logger.info(f"Stored episodic memory: {event_name} (ID: {episode_id})")
            return episode_id
    
    def get_recent_episodes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent episodic memories"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM episodic_memory 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_episodes(self, query: str) -> List[Dict[str, Any]]:
        """Search episodic memories"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM episodic_memory 
                WHERE event_name LIKE ? OR description LIKE ?
                ORDER BY timestamp DESC
            """, (f"%{query}%", f"%{query}%"))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== SEMANTIC MEMORY =====
    
    def store_fact(
        self,
        fact_type: str,
        key: str,
        value: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a semantic memory (fact/knowledge)
        
        Args:
            fact_type: Type of fact (e.g., "preference", "knowledge", "configuration")
            key: Unique key for the fact
            value: Fact value
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            
        Returns:
            ID of stored fact
        """
        with self.lock:
            cursor = self.connection.cursor()
            metadata_str = json.dumps(metadata) if metadata else None
            
            try:
                cursor.execute("""
                    INSERT INTO semantic_memory 
                    (fact_type, key, value, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (fact_type, key, value, confidence, metadata_str))
            except sqlite3.IntegrityError:
                # Update existing fact
                cursor.execute("""
                    UPDATE semantic_memory 
                    SET value = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP, metadata = ?
                    WHERE key = ?
                """, (value, confidence, metadata_str, key))
            
            self.connection.commit()
            logger.info(f"Stored semantic memory: {key} = {value}")
            return cursor.lastrowid
    
    def get_fact(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific fact"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM semantic_memory WHERE key = ?", (key,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_facts_by_type(self, fact_type: str) -> List[Dict[str, Any]]:
        """Get all facts of a specific type"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM semantic_memory WHERE fact_type = ?", (fact_type,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_facts(self) -> List[Dict[str, Any]]:
        """Get all semantic facts"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM semantic_memory")
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== PROCEDURAL MEMORY =====
    
    def store_procedure(
        self,
        procedure_name: str,
        description: str,
        steps: List[str],
        frequency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a procedural memory (workflow/routine)
        
        Args:
            procedure_name: Name of the procedure
            description: Description of the procedure
            steps: List of steps to follow
            frequency: How often it's done (daily, weekly, etc.)
            metadata: Additional metadata
            
        Returns:
            ID of stored procedure
        """
        with self.lock:
            cursor = self.connection.cursor()
            steps_str = json.dumps(steps)
            metadata_str = json.dumps(metadata) if metadata else None
            
            try:
                cursor.execute("""
                    INSERT INTO procedural_memory 
                    (procedure_name, description, steps, frequency, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (procedure_name, description, steps_str, frequency, metadata_str))
            except sqlite3.IntegrityError:
                cursor.execute("""
                    UPDATE procedural_memory 
                    SET description = ?, steps = ?, frequency = ?, metadata = ?
                    WHERE procedure_name = ?
                """, (description, steps_str, frequency, metadata_str, procedure_name))
            
            self.connection.commit()
            logger.info(f"Stored procedural memory: {procedure_name}")
            return cursor.lastrowid
    
    def get_procedure(self, procedure_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific procedure"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM procedural_memory WHERE procedure_name = ?", (procedure_name,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['steps'] = json.loads(result['steps']) if result['steps'] else []
                return result
            return None
    
    def get_all_procedures(self) -> List[Dict[str, Any]]:
        """Get all procedures"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM procedural_memory ORDER BY procedure_name")
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['steps'] = json.loads(result['steps']) if result['steps'] else []
                results.append(result)
            return results
    
    def log_procedure_execution(self, procedure_name: str, success: bool):
        """Log procedure execution"""
        with self.lock:
            cursor = self.connection.cursor()
            if success:
                cursor.execute("""
                    UPDATE procedural_memory 
                    SET success_count = success_count + 1, last_executed = CURRENT_TIMESTAMP
                    WHERE procedure_name = ?
                """, (procedure_name,))
            else:
                cursor.execute("""
                    UPDATE procedural_memory 
                    SET fail_count = fail_count + 1
                    WHERE procedure_name = ?
                """, (procedure_name,))
            
            self.connection.commit()
    
    # ===== RELATIONSHIP GRAPH =====
    
    def create_relationship(
        self,
        entity_a: str,
        entity_b: str,
        relationship_type: str,
        strength: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a relationship between two entities
        
        Args:
            entity_a: First entity
            entity_b: Second entity
            relationship_type: Type of relationship
            strength: Relationship strength (0-1)
            metadata: Additional metadata
            
        Returns:
            ID of relationship
        """
        with self.lock:
            cursor = self.connection.cursor()
            metadata_str = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO relationships 
                (entity_a, entity_b, relationship_type, strength, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (entity_a, entity_b, relationship_type, strength, metadata_str))
            
            self.connection.commit()
            logger.info(f"Created relationship: {entity_a} -{relationship_type}-> {entity_b}")
            return cursor.lastrowid
    
    def get_entity_relationships(self, entity: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM relationships 
                WHERE entity_a = ? OR entity_b = ?
                ORDER BY strength DESC
            """, (entity, entity))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_relationship_graph(self) -> Dict[str, Any]:
        """Get the complete relationship graph"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM relationships ORDER BY strength DESC")
            
            graph = {
                "edges": [dict(row) for row in cursor.fetchall()],
                "node_count": self._count_unique_entities(),
            }
            return graph
    
    def _count_unique_entities(self) -> int:
        """Count unique entities in relationships"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT entity) FROM (
                    SELECT entity_a as entity FROM relationships
                    UNION
                    SELECT entity_b as entity FROM relationships
                )
            """)
            return cursor.fetchone()[0]
    
    # ===== LEGACY SUPPORT =====
    
    def save(self, category: str, content: str):
        """Legacy save method for backward compatibility"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO memory (category, content) VALUES (?, ?)",
                (category, content)
            )
            self.connection.commit()
    
    def get_recent(self, limit: int = 10):
        """Legacy get_recent for backward compatibility"""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT category, content, created_at FROM memory ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()
    
    # ===== UTILITY =====
    
    def close(self):
        """Close database connection"""
        with self.lock:
            self.connection.close()
            logger.info("Memory database closed")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        with self.lock:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM episodic_memory")
            episodic_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM semantic_memory")
            semantic_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM procedural_memory")
            procedural_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM relationships")
            relationships_count = cursor.fetchone()[0]
            
            return {
                "episodic_memories": episodic_count,
                "semantic_facts": semantic_count,
                "procedures": procedural_count,
                "relationships": relationships_count,
                "total_memories": episodic_count + semantic_count + procedural_count,
            }
