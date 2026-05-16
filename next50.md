# Friday — Next 50% Architecture Evolution

## Goal

Transform Friday from:

```txt
Command Assistant
```

into:

```txt
Cognitive AI Agent System
```

The next evolution focuses on:

* reasoning
* planning
* memory intelligence
* autonomous execution
* natural conversation
* adaptive behavior
* emotional interaction
* long-term personalization

---

# Final Target Architecture

```txt
User
 ↓
Voice/Text/Vision Input
 ↓
Perception Layer
 ↓
Context & Memory Layer
 ↓
Reasoning Engine (LLM Agent)
 ↓
Planner / Decision Engine
 ↓
Tool Orchestration Layer
 ↓
Execution Layer
 ↓
Reflection / Self-Correction
 ↓
Personality & Response Engine
 ↓
Neural TTS
 ↓
User
```

---

# Phase 1 — Perception Layer

Current system:

* STT
* CLI
* Wake word

Next upgrade:

* intent understanding
* emotional understanding
* contextual extraction
* semantic parsing

---

## New Folder Structure

```txt
perception/
 ├── speech_understanding.py
 ├── intent_classifier.py
 ├── emotion_detector.py
 ├── context_extractor.py
 ├── entity_extractor.py
 └── multimodal_router.py
```

---

## Responsibilities

### speech_understanding.py

* semantic understanding of transcribed speech
* cleanup and normalization
* conversational parsing

### intent_classifier.py

Converts user requests into structured intents.

Example:

```json
{
  "intent": "play_music",
  "confidence": 0.95
}
```

### emotion_detector.py

Detects:

* tiredness
* urgency
* frustration
* happiness
* calmness

This enables emotional responses.

### context_extractor.py

Extracts:

* entities
* goals
* references
* temporal context

Example:

```txt
"Open the file from yesterday"
```

Extracts:

* target=file
* time=yesterday

### multimodal_router.py

Routes:

* text
* voice
* future vision inputs

---

# Phase 2 — Cognitive Memory System

Current system stores memory.

Next upgrade:

* memory reasoning
* relationship mapping
* contextual retrieval
* behavioral learning

---

## New Architecture

```txt
memory/
 ├── episodic/
 ├── semantic/
 ├── procedural/
 ├── embeddings/
 ├── retrieval/
 ├── summarization/
 ├── personality_memory/
 └── relationship_graph/
```

---

## Memory Types

### Episodic Memory

Stores experiences.

Example:

```txt
User worked on Neo4j yesterday.
```

---

### Semantic Memory

Stores facts.

Example:

```txt
User uses Arch Linux.
```

---

### Procedural Memory

Stores workflows.

Example:

```txt
Every evening:
- open VSCode
- open Spotify
- launch terminal
```

Assistant can automate routines.

---

### Relationship Graph

Uses graph structures for contextual intelligence.

Example:

```txt
User
 ├── likes → Cori voice
 ├── works_on → Friday project
 ├── uses → Arch Linux
 └── studies → JavaScript
```

Enables relationship-based reasoning.

---

# Phase 3 — Reasoning Engine

Current system:

```txt
Router → if/else commands
```

Upgrade to:

```txt
LLM Agent
 ↓
Reasoning
 ↓
Planning
 ↓
Tool Selection
```

---

## New Folder Structure

```txt
brain/
 ├── planner.py
 ├── tool_selector.py
 ├── reasoning_engine.py
 ├── task_decomposer.py
 ├── reflection_engine.py
 ├── conversation_engine.py
 └── autonomous_executor.py
```

---

## Responsibilities

### planner.py

Breaks large tasks into subtasks.

Example:

```txt
"Prepare coding environment"
```

Becomes:

1. Open VSCode
2. Open terminal
3. Launch Spotify
4. Open browser tabs
5. Enable DND

---

### tool_selector.py

Chooses correct tools dynamically.

No hardcoded routing.

---

### reasoning_engine.py

Handles:

* chain-of-thought style planning
* contextual understanding
* decision-making
* ambiguity handling

---

### task_decomposer.py

Splits complex goals into executable actions.

---

### reflection_engine.py

Self-checking and recovery.

Example:

```txt
Action failed
 → retry
 → rethink
 → ask user
```

---

### autonomous_executor.py

Handles multi-step autonomous tasks.

---

# Phase 4 — Tool Calling System

Replace command maps with dynamic tool orchestration.

---

## New Tool Architecture

```txt
tools/
 ├── browser/
 ├── linux/
 ├── filesystem/
 ├── media/
 ├── internet/
 ├── coding/
 ├── adb/
 ├── vision/
 └── communication/
```

---

## Tool Registry Example

```json
{
  "name": "browser.open_url",
  "description": "Open a website in the browser",
  "parameters": {
    "url": "string"
  }
}
```

LLM dynamically selects tools.

---

# Phase 5 — Reflection & Self-Correction

Critical for intelligent behavior.

---

## Reflection Loop

```txt
Execute Action
 ↓
Observe Result
 ↓
Did it succeed?
 ↓
If no:
  retry / rethink / ask user
```

---

## Example

```txt
Assistant: Opening Firefox...
```

If launch fails:

* detect failure
* retry
* explain problem
* suggest alternatives

---

# Phase 6 — Autonomous Task Engine

Enables long-running intelligent workflows.

---

## Example

```txt
"Download Python courses and organize them"
```

Agent can:

* search
* download
* extract
* categorize
* rename
* organize
* summarize

---

## Folder Structure

```txt
task_engine/
 ├── scheduler.py
 ├── workflow_graph.py
 ├── dependency_manager.py
 ├── retry_manager.py
 └── async_executor.py
```

---

# Phase 7 — Human-Like Conversation System

This layer creates realism.

---

## Folder Structure

```txt
personality/
 ├── speech_styler.py
 ├── emotion_engine.py
 ├── response_humanizer.py
 ├── pacing_controller.py
 ├── tone_selector.py
 └── conversational_memory.py
```

---

## Responsibilities

### speech_styler.py

Transforms robotic responses into natural speech.

Example:

Before:

```txt
Opening Firefox.
```

After:

```txt
Sure… opening Firefox now.
```

---

### pacing_controller.py

Controls:

* pauses
* delays
* rhythm
* conversational timing

---

### emotion_engine.py

Selects speaking style based on:

* user emotion
* context
* urgency
* environment

---

### response_humanizer.py

Adds:

* conversational flow
* natural phrasing
* realistic transitions
* emotional softness

---

# Phase 8 — Advanced Voice System

Current voice systems are too robotic.

Upgrade pipeline:

```txt
LLM Response
 ↓
Speech Styler
 ↓
Emotion Formatter
 ↓
Neural TTS
 ↓
Audio Effects
 ↓
Playback Engine
```

---

## Recommended Stack

### STT

* Whisper.cpp

### TTS

* TTS
* Piper high-quality voices (piper cori-high female voice)

### Audio FX

* ffmpeg filters
* realtime audio processing
* subtle reverb
* wake sounds
* interruption smoothing

---

# Phase 9 — Vision System

Future multimodal upgrade.

---

## Folder Structure

```txt
vision/
 ├── screen_understanding.py
 ├── OCR_engine.py
 ├── object_detector.py
 ├── UI_parser.py
 └── webcam_context.py
```

---

## Capabilities

Assistant can:

* understand screens
* parse interfaces
* read text from images
* analyze visual context
* guide users visually

---

# Phase 10 — Self-Learning System

Final evolution.

Assistant learns:

* habits
* schedules
* routines
* preferred tools
* speaking style
* work patterns

---

## Example

```txt
Every evening:
- open VSCode
- open terminal
- play lo-fi music
```

Assistant eventually suggests or automates workflows.

---

# Final System Architecture

```txt
Perception Layer
 ↓
Context Builder
 ↓
Memory System
 ↓
Reasoning Agent
 ↓
Planner
 ↓
Tool Selector
 ↓
Execution Engine
 ↓
Reflection Loop
 ↓
Personality Engine
 ↓
Voice System
 ↓
User
```

---

# Recommended Priority Order

Do NOT build everything at once.

Highest-impact upgrades first:

1. LLM tool calling
2. Memory reasoning
3. Speech humanization
4. Reflection loop
5. Planner system
6. Autonomous tasks
7. Vision integration
8. Self-learning system

---

# Current Implementation Status

Completed:

* LLM tool calling system
* Memory reasoning and relational memory
* Speech humanization / personality response styling
* Reflection and self-correction loop
* Piper voice support for `cori-high`

Remaining work:

* Planner system and task decomposition
* Tool selector and decision engine
* Autonomous task engine / workflow orchestration
* Vision system scaffolding and screen understanding
* Self-learning system for habits, routines, and preferences
* Perception layer enhancements for intent, emotion, and contextual extraction
* Memory stack expansion for embeddings, retrieval, summarization, and personality memory
* Tool architecture expansion for internet, adb, communication, and vision tools

## Next Focus

1. Build `brain/planner.py` and `brain/task_decomposer.py`
2. Create `brain/tool_selector.py` and `brain/autonomous_executor.py`
3. Add `task_engine/` workflow orchestration modules
4. Extend `vision/` for multimodal understanding
5. Add self-learning routines and continuous personalization

---

# Long-Term Vision

Friday evolves into:

* local AI operating system
* autonomous Linux assistant
* intelligent workflow orchestrator
* multimodal AI companion
* context-aware productivity system
* adaptive cognitive agent

---

# Core Philosophy

The assistant should not:

* blindly execute commands
* rely on fixed keywords
* behave like a chatbot

The assistant should:

* understand intent
* reason about goals
* plan actions
* adapt to context
* remember patterns
* speak naturally
* learn continuously

That is the transition from:

```txt
Assistant
```

into:

```txt
Cognitive AI System
```
