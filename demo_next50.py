"""
Demo script for Friday's new tool calling and memory reasoning systems
Shows how to use the LLM tool calling, memory system, and reasoning agent
"""

import asyncio
from pathlib import Path
import sys

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from brain.llm import FridayLLM
from brain.reasoning_agent import ReasoningAgent
from brain.memory_reasoning_engine import MemoryReasoningEngine
from memory.enhanced_memory import EnhancedMemoryDatabase
from personality import ResponseHumanizer
from tools.tool_loader import create_tool_system
from loguru import logger


async def demo_tool_system():
    """Demonstrate the tool calling system"""
    print("\n" + "="*60)
    print("DEMO 1: Tool Calling System")
    print("="*60)
    
    # Create tool system
    registry, orchestrator = create_tool_system()
    
    print(f"\n✓ Loaded {len(registry.list_tools())} tools")
    print("\nAvailable tool categories:")
    for category in registry.list_categories():
        tools = registry.get_by_category(category)
        print(f"  {category}: {len(tools)} tools")
        for tool in tools:
            print(f"    - {tool.name}")
    
    # Show tool schema
    print("\nExample tool schema:")
    schemas = registry.get_schemas()[:3]
    for schema in schemas:
        print(f"\n  Tool: {schema['name']}")
        print(f"  Description: {schema['description']}")
        print(f"  Parameters: {', '.join([p['name'] for p in schema['parameters']])}")


async def demo_memory_system():
    """Demonstrate the enhanced memory system"""
    print("\n" + "="*60)
    print("DEMO 2: Enhanced Memory System")
    print("="*60)
    
    # Create memory database
    memory_db = EnhancedMemoryDatabase(path=":memory:")  # Use in-memory DB for demo
    
    # Store episodic memory (experiences)
    print("\n1. Storing Episodic Memory (Experiences)...")
    memory_db.store_episode(
        event_name="Coding Session",
        description="User worked on the Friday project for 2 hours",
        importance=0.8,
        tags=["coding", "python", "friday"]
    )
    memory_db.store_episode(
        event_name="Music Listening",
        description="User listened to lo-fi music while coding",
        importance=0.6,
        tags=["music", "spotify", "lo-fi"]
    )
    
    recent = memory_db.get_recent_episodes()
    print(f"   ✓ Stored {len(recent)} episodes")
    
    # Store semantic memory (facts)
    print("\n2. Storing Semantic Memory (Facts)...")
    memory_db.store_fact("preference", "favorite_music", "lo-fi hip hop")
    memory_db.store_fact("configuration", "os", "Arch Linux")
    memory_db.store_fact("skill", "programming_language", "Python")
    
    facts = memory_db.get_all_facts()
    print(f"   ✓ Stored {len(facts)} facts")
    for fact in facts:
        print(f"     - {fact['key']}: {fact['value']}")
    
    # Store procedural memory (routines)
    print("\n3. Storing Procedural Memory (Routines)...")
    memory_db.store_procedure(
        procedure_name="Morning Setup",
        description="Daily morning development environment setup",
        steps=[
            "Open VSCode",
            "Open Terminal",
            "Start Spotify with lo-fi playlist",
            "Check system status"
        ],
        frequency="daily"
    )
    
    procedures = memory_db.get_all_procedures()
    print(f"   ✓ Stored {len(procedures)} procedures")
    
    # Create relationships
    print("\n4. Creating Relationships...")
    memory_db.create_relationship("User", "Friday Project", "works_on", strength=0.9)
    memory_db.create_relationship("User", "lo-fi music", "likes", strength=0.8)
    memory_db.create_relationship("User", "Arch Linux", "uses", strength=0.95)
    
    graph = memory_db.get_relationship_graph()
    print(f"   ✓ Created relationship graph with {graph['node_count']} nodes")
    
    # Display statistics
    print("\n5. Memory Statistics:")
    stats = memory_db.get_statistics()
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    return memory_db


async def demo_memory_reasoning():
    """Demonstrate memory reasoning engine"""
    print("\n" + "="*60)
    print("DEMO 3: Memory Reasoning Engine")
    print("="*60)
    
    # Create and populate memory
    memory_db = EnhancedMemoryDatabase(path=":memory:")
    reasoning_engine = MemoryReasoningEngine(memory_db)
    
    # Record experiences
    print("\n1. Recording Experiences...")
    reasoning_engine.record_experience(
        event_name="Project Started",
        description="Friday Cognitive AI Agent system development began",
        importance=0.9,
        tags=["project", "ai", "development"]
    )
    
    # Learn facts
    print("2. Learning Facts...")
    reasoning_engine.learn_fact("preference", "editor", "VSCode", confidence=0.95)
    reasoning_engine.learn_fact("preference", "terminal", "tmux", confidence=0.85)
    reasoning_engine.learn_fact("skill", "language", "Python", confidence=0.9)
    
    # Establish routines
    print("3. Establishing Routines...")
    reasoning_engine.establish_routine(
        procedure_name="Code Review Ritual",
        description="Regular code review and refactoring process",
        steps=["Read recent changes", "Check tests", "Optimize code", "Document changes"],
        frequency="weekly"
    )
    
    # Link entities
    print("4. Linking Entities...")
    reasoning_engine.link_entities("VSCode", "Friday", "used_for", strength=0.9)
    reasoning_engine.link_entities("Python", "Friday", "primary_language", strength=0.95)
    
    # Test reasoning
    print("\n5. Testing Reasoning...")
    context = reasoning_engine.build_context("Tell me about Friday project")
    print(f"   Context retrieved: {len(context['relationships'])} relationships")
    
    # Get session summary
    summary = reasoning_engine.get_session_summary()
    print(f"\n6. Session Summary:")
    print(f"   - Messages: {summary['messages']}")
    print(f"   - Memory stats: {summary['memory_stats']}")


async def demo_response_humanizer():
    """Demonstrate response humanization"""
    print("\n" + "="*60)
    print("DEMO 4: Response Humanizer")
    print("="*60)
    
    humanizer = ResponseHumanizer()
    sample_response = "Opening Firefox. I have launched the application and it should appear shortly."
    humanized = humanizer.humanize_response(sample_response, emotion=None, style=None, add_pacing=True)
    
    print("\nOriginal:")
    print(f"  {sample_response}")
    print("\nHumanized:")
    print(f"  {humanized}")
    
    summary = humanizer.get_conversation_summary()
    print("\nHumanizer Summary:")
    print(f"  {summary}")


async def demo_llm_with_tools():
    """Demonstrate LLM with tool context"""
    print("\n" + "="*60)
    print("DEMO 4: LLM with Tool Context")
    print("="*60)
    
    # Create tool system and LLM
    registry, orchestrator = create_tool_system()
    llm = FridayLLM(tool_registry=registry)
    
    print("\n1. System Prompt with Tool Information:")
    prompt_lines = llm.system_prompt.split('\n')
    print(f"   System prompt length: {len(prompt_lines)} lines")
    print("   First 5 lines:")
    for line in prompt_lines[:5]:
        if line.strip():
            print(f"   {line[:70]}...")
    
    print("\n2. Available Tools in LLM Context:")
    print(f"   Total tools: {len(registry.list_tools())}")
    print("   Categories:", ", ".join(registry.list_categories()))
    
    print("\n3. Tool Orchestration Ready:")
    print(f"   Registry status: ✓ {len(registry.list_tools())} tools")
    print(f"   Orchestrator status: ✓ Ready for execution")


async def demo_reasoning_agent():
    """Demonstrate the reasoning agent"""
    print("\n" + "="*60)
    print("DEMO 5: Reasoning Agent")
    print("="*60)
    
    # Create all systems
    memory_db = EnhancedMemoryDatabase(path=":memory:")
    memory_engine = MemoryReasoningEngine(memory_db)
    registry, orchestrator = create_tool_system()
    llm = FridayLLM(tool_registry=registry)
    reasoning_agent = ReasoningAgent(llm, orchestrator)
    
    print("\n1. Reasoning Agent Initialized:")
    print(f"   ✓ LLM: {llm.model}")
    print(f"   ✓ Tools: {len(registry.list_tools())}")
    print(f"   ✓ Max iterations: {reasoning_agent.max_tool_iterations}")
    
    print("\n2. Reasoning Agent Capabilities:")
    print("   - Multi-turn conversation with tool context")
    print("   - Automatic tool selection based on request")
    print("   - Reflection and self-correction")
    print("   - Conversation history tracking")
    
    print("\n3. Agent Status:")
    summary = reasoning_agent.get_tool_summary()
    print(f"   Total tool calls: {summary['total_calls']}")
    print(f"   Success rate: {summary['success_rate']:.1%}")


async def main():
    """Run all demos"""
    logger.info("Starting Friday System Demo")
    
    try:
        # Run demos
        await demo_tool_system()
        await demo_memory_system()
        await demo_memory_reasoning()
        await demo_response_humanizer()
        await demo_llm_with_tools()
        await demo_reasoning_agent()
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("\nSummary of Implemented Features:")
        print("✓ Tool Calling System (22 tools)")
        print("✓ Enhanced Memory (Episodic, Semantic, Procedural)")
        print("✓ Relationship Graph")
        print("✓ Memory Reasoning Engine")
        print("✓ LLM Tool Integration")
        print("✓ Reasoning Agent")
        print("\nNext Phase: Speech Humanization & Reflection Loop")
        
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        print(f"\nError during demo: {e}")


if __name__ == "__main__":
    asyncio.run(main())
