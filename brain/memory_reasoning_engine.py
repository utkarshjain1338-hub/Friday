"""
Memory Reasoning Engine
Uses multiple memory types for context-aware intelligent reasoning
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from loguru import logger
from datetime import datetime, timedelta
from .enhanced_memory import EnhancedMemoryDatabase
import json


class MemoryReasoningEngine:
    """
    Cognitive engine that reasons using episodic, semantic, and procedural memory
    """
    
    def __init__(self, memory_db: EnhancedMemoryDatabase):
        self.memory = memory_db
        self.context_window = []
        self.max_context_size = 100
        logger.info("Memory reasoning engine initialized")
    
    # ===== CONTEXT BUILDING =====
    
    def build_context(self, query: str, max_memories: int = 5) -> Dict[str, Any]:
        """
        Build contextual information from all memory types
        
        Args:
            query: User query
            max_memories: Max memories to include
            
        Returns:
            Context dictionary with relevant memories
        """
        context = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "episodic": self._get_relevant_episodes(query, max_memories),
            "semantic": self._get_relevant_facts(query, max_memories),
            "procedural": self._get_relevant_procedures(query, max_memories),
            "relationships": self._extract_relationships_for_query(query),
        }
        
        # Add to context window
        self.context_window.append(context)
        if len(self.context_window) > self.max_context_size:
            self.context_window.pop(0)
        
        return context
    
    def _get_relevant_episodes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant episodic memories for query"""
        query_lower = query.lower()
        episodes = self.memory.get_recent_episodes(limit=50)
        
        relevant = []
        for episode in episodes:
            if self._matches_query(query_lower, episode.get("event_name", ""), episode.get("description", "")):
                relevant.append({
                    "event": episode.get("event_name"),
                    "when": episode.get("timestamp"),
                    "importance": episode.get("importance"),
                    "tags": json.loads(episode.get("tags", "[]")) if episode.get("tags") else [],
                })
                if len(relevant) >= limit:
                    break
        
        return relevant
    
    def _get_relevant_facts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant semantic facts for query"""
        query_lower = query.lower()
        facts = self.memory.get_all_facts()
        
        relevant = []
        for fact in facts:
            if self._matches_query(query_lower, fact.get("key", ""), fact.get("value", "")):
                relevant.append({
                    "type": fact.get("fact_type"),
                    "key": fact.get("key"),
                    "value": fact.get("value"),
                    "confidence": fact.get("confidence"),
                })
                if len(relevant) >= limit:
                    break
        
        return relevant
    
    def _get_relevant_procedures(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get relevant procedural memories for query"""
        query_lower = query.lower()
        procedures = self.memory.get_all_procedures()
        
        relevant = []
        for proc in procedures:
            if self._matches_query(query_lower, proc.get("procedure_name", ""), proc.get("description", "")):
                relevant.append({
                    "name": proc.get("procedure_name"),
                    "description": proc.get("description"),
                    "frequency": proc.get("frequency"),
                    "success_rate": self._calculate_success_rate(proc),
                })
                if len(relevant) >= limit:
                    break
        
        return relevant
    
    def _extract_relationships_for_query(self, query: str) -> List[Dict[str, Any]]:
        """Extract relevant entities and relationships from query"""
        # Simple entity extraction (can be enhanced)
        entities = self._extract_entities_from_query(query)
        relationships = []
        
        for entity in entities:
            rels = self.memory.get_entity_relationships(entity)
            relationships.extend([
                {
                    "from": r.get("entity_a"),
                    "to": r.get("entity_b"),
                    "type": r.get("relationship_type"),
                    "strength": r.get("strength"),
                }
                for r in rels
            ])
        
        return relationships[:10]  # Limit to 10 relationships
    
    def _extract_entities_from_query(self, query: str) -> Set[str]:
        """Extract entities from query"""
        # Simple noun-like extraction (can be enhanced with NLP)
        words = query.lower().split()
        entities = set()
        
        # Look for capitalized words or specific patterns
        for word in query.split():
            if word[0].isupper():
                entities.add(word)
        
        # Common entities
        for keyword in ["vscode", "firefox", "spotify", "python", "javascript", "arch linux"]:
            if keyword in query.lower():
                entities.add(keyword)
        
        return entities
    
    @staticmethod
    def _matches_query(query_lower: str, field1: str, field2: str) -> bool:
        """Check if query matches fields"""
        field1_lower = field1.lower()
        field2_lower = field2.lower()
        
        # Split query into keywords
        keywords = query_lower.split()
        
        for keyword in keywords:
            if len(keyword) > 3:  # Only check significant words
                if keyword in field1_lower or keyword in field2_lower:
                    return True
        
        return False
    
    @staticmethod
    def _calculate_success_rate(procedure: Dict[str, Any]) -> float:
        """Calculate procedure success rate"""
        success = procedure.get("success_count", 0)
        fail = procedure.get("fail_count", 0)
        total = success + fail
        
        if total == 0:
            return 0.5  # Default for untested procedures
        
        return success / total
    
    # ===== MEMORY UPDATES =====
    
    def record_experience(
        self,
        event_name: str,
        description: str,
        context: Optional[str] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None
    ):
        """Record a user experience"""
        self.memory.store_episode(
            event_name=event_name,
            description=description,
            context=context,
            importance=importance,
            tags=tags
        )
    
    def learn_fact(self, fact_type: str, key: str, value: str, confidence: float = 1.0):
        """Learn and store a fact"""
        self.memory.store_fact(
            fact_type=fact_type,
            key=key,
            value=value,
            confidence=confidence
        )
    
    def establish_routine(
        self,
        procedure_name: str,
        description: str,
        steps: List[str],
        frequency: Optional[str] = None
    ):
        """Establish a routine/procedure"""
        self.memory.store_procedure(
            procedure_name=procedure_name,
            description=description,
            steps=steps,
            frequency=frequency
        )
    
    def link_entities(self, entity_a: str, entity_b: str, relationship_type: str, strength: float = 0.5):
        """Create relationship between entities"""
        self.memory.create_relationship(
            entity_a=entity_a,
            entity_b=entity_b,
            relationship_type=relationship_type,
            strength=strength
        )
    
    # ===== REASONING QUERIES =====
    
    def answer_what_question(self, query: str) -> str:
        """Answer 'What' questions using semantic memory"""
        context = self.build_context(query, max_memories=3)
        facts = context.get("semantic", [])
        
        if facts:
            response = "Based on what I know: "
            for fact in facts[:2]:
                response += f"{fact['value']} "
            return response
        
        return "I don't have information about that yet."
    
    def answer_when_question(self, query: str) -> str:
        """Answer 'When' questions using episodic memory"""
        context = self.build_context(query, max_memories=3)
        episodes = context.get("episodic", [])
        
        if episodes:
            response = "From my memory: "
            for episode in episodes[:2]:
                response += f"{episode['event']} ({episode['when']}) "
            return response
        
        return "I don't recall when that happened."
    
    def answer_how_question(self, query: str) -> str:
        """Answer 'How' questions using procedural memory"""
        context = self.build_context(query, max_memories=3)
        procedures = context.get("procedural", [])
        
        if procedures:
            response = "Here's how to do it: "
            for proc in procedures[:1]:
                response += f"{proc['description']} "
            return response
        
        return "I don't have a procedure for that yet."
    
    def suggest_action(self, query: str) -> Optional[str]:
        """Suggest an action based on context and relationships"""
        context = self.build_context(query, max_memories=5)
        relationships = context.get("relationships", [])
        facts = context.get("semantic", [])
        
        # Look for actionable relationships
        for rel in relationships:
            if rel["type"] in ["works_on", "likes", "uses"]:
                return f"You usually work on {rel['to']}"
        
        return None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.context_window:
            return {"messages": 0, "contexts": []}
        
        return {
            "messages": len(self.context_window),
            "first_query": self.context_window[0].get("query"),
            "last_query": self.context_window[-1].get("query"),
            "memory_stats": self.memory.get_statistics(),
        }
    
    # ===== MEMORY CONSOLIDATION =====
    
    def consolidate_memories(self):
        """Periodically consolidate and summarize memories"""
        stats = self.memory.get_statistics()
        logger.info(f"Memory consolidation: {stats}")
        
        # Could implement memory summarization, forgetting, or reorganization here
        # For now, just log the stats
    
    def get_memory_insights(self) -> Dict[str, Any]:
        """Get insights from memory system"""
        graph = self.memory.get_relationship_graph()
        stats = self.memory.get_statistics()
        
        insights = {
            "stats": stats,
            "relationship_density": len(graph["edges"]) / max(graph["node_count"], 1) if graph["node_count"] > 0 else 0,
            "top_relationships": sorted(graph["edges"], key=lambda x: x.get("strength", 0), reverse=True)[:5],
        }
        
        return insights
