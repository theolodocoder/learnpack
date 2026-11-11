# Agent frameworks: when to use one

## Why this matters

Job posts and client briefs name frameworks: "experience with LangGraph", "built on the Claude Agent SDK". You need to know what these tools actually give you, what they cost, and how to decide whether a project needs one, so you can use them when they help, explain why when they don't, and debug them when they break. Because you've written the loop, state handling and approval gates by hand, you can now see exactly which of those pieces a framework replaces.

## 1. What a framework adds

Everything an agent framework does, you've already done by hand in this section. A framework packages it:

| Concern | By hand (this section) | What a framework offers |
|---|---|---|
| The loop | `for turn in range(max_turns)` with stop-reason handling | Built-in loop with sensible defaults |
| Tools | A registry from type hints | Decorators, plus ready-made tools (files, shell, web search, MCP servers) |
| Control flow | `if`/`while` in Python | A **graph** of nodes and edges you can draw and inspect |
| State | A Pydantic `TaskState` you save | A typed state object updated by each step |
| Persistence and resume | JSON file per task | **Checkpoints** saved after every step, keyed by a thread id |
| Human approval | Save state, stop, resume on click | **Interrupts**: pause inside a step, resume with the human's answer |
| Observability | JSON log lines | **Tracing**: every model call, tool call, input, output and timing in a UI |
| Multi-agent | Calling one agent from another | Subagents, handoffs, supervisor patterns |

None of this is magic, but it's real work: checkpointing correctly, resuming mid-step, and a trace viewer would take you weeks to build well.

## 2. The graph idea, in plain Python

The core idea of LangGraph is to describe an agent as a **state graph**:

- **State:** a dict (or typed dict) shared by all steps.
- **Nodes:** functions that take the state and return **updates** to it.
- **Edges:** which node runs next. A **conditional edge** calls a function on the state to decide.
- **Checkpoint:** a snapshot of the state after each node, so a run can be inspected, replayed or resumed.

You can build the engine in about 30 lines, which is the best way to understand what a framework is doing:

```python
END = "__end__"


class Graph:
    def __init__(self):
        self.nodes, self.edges, self.routers, self.entry = {}, {}, {}, None

    def add_node(self, name, fn): self.nodes[name] = fn
    def add_edge(self, src, dst): self.edges[src] = dst
    def add_conditional_edge(self, src, router): self.routers[src] = router
    def set_entry(self, name): self.entry = name

    def run(self, state, max_steps=25, checkpoints=None):
        state, current = dict(state), self.entry
        for _ in range(max_steps):
            state = {**state, **self.nodes[current](state)}       # run node, merge its updates
            if checkpoints is not None:
                checkpoints.append((current, dict(state)))           # snapshot after every step
            current = self.routers[current](state) if current in self.routers else self.edges[current]
            if current == END:
                return state
        raise RuntimeError("step budget exhausted")
```

An evaluator–optimiser loop (from *What agents are, and when you need one*) becomes a graph with a cycle:

```python
def write(state):
    draft = call_claude(f"Write a product description for {state['product']}. "
                        f"Feedback to address: {state.get('feedback', 'none')}")
    return {"draft": draft, "attempts": state.get("attempts", 0) + 1}

def review(state):
    verdict = judge(state["draft"])          # e.g. an LLM judge with structured output
    return {"approved": verdict.passed, "feedback": verdict.reasoning}

g = Graph()
g.add_node("write", write)
g.add_node("review", review)
g.set_entry("write")
g.add_edge("write", "review")
g.add_conditional_edge("review", lambda s: END if s["approved"] or s["attempts"] >= 3 else "write")

saved = []
final = g.run({"product": "solar lantern"}, checkpoints=saved)
print([name for name, _ in saved])   # ['write', 'review', 'write', 'review']
```

Look at what the graph gives you over a `while` loop: the structure is **data**, so a tool can draw it, log each node by name, and save state at every boundary. That's what checkpoints, tracing and resume are built on.

## 3. LangGraph's version

Here is the same pattern in LangGraph. It isn't installed in this environment, so read this as illustration; you won't run it in the exercises. Note how closely it maps to the plain version:

```python
# pip install langgraph   (illustrative: not used in the exercises)
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict, total=False):
    product: str
    draft: str
    feedback: str
    approved: bool
    attempts: int


def write(state: State) -> dict:
    ...  # call Claude, return {"draft": ..., "attempts": ...}

def review(state: State) -> dict:
    ...  # judge the draft, return {"approved": ..., "feedback": ...}

def after_review(state: State) -> str:
    return END if state["approved"] or state["attempts"] >= 3 else "write"


builder = StateGraph(State)
builder.add_node("write", write)
builder.add_node("review", review)
builder.add_edge(START, "write")
builder.add_edge("write", "review")
builder.add_conditional_edges("review", after_review)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "lantern-1"}}
result = graph.invoke({"product": "solar lantern"}, config)
```

The pieces to recognise:

- **`StateGraph(State)`** with a `TypedDict` state; nodes return partial updates that get merged.
- **`START` / `END`** as special nodes; `add_conditional_edges` takes a routing function.
- **`compile(checkpointer=...)`** turns on persistence. `InMemorySaver` keeps checkpoints in memory; production setups use a database-backed saver (Postgres, SQLite).
- **`thread_id`** in the config identifies a run. Invoke again with the same thread id and LangGraph loads the saved state.

### Interrupts: human approval as a pause

LangGraph's version of the approval-gate-plus-resume pattern from *Humans in the loop*:

```python
from langgraph.types import Command, interrupt


def send_refund(state: State) -> dict:
    answer = interrupt({"action": "refund", "order": state["order_id"], "amount": state["amount"]})
    if answer != "approve":
        return {"result": "refund denied by reviewer"}
    return {"result": do_refund(state["order_id"], state["amount"])}


# First invoke runs until interrupt() and pauses; the checkpoint is saved under the thread id.
result = graph.invoke({"order_id": "A1", "amount": 40}, config)
print(result["__interrupt__"])           # what the reviewer needs to see

# Later (another request, even another server), resume with the human's answer:
result = graph.invoke(Command(resume="approve"), config)
```

The value passed in `Command(resume=...)` becomes the return value of `interrupt()`. It's exactly what you'd build by hand: save state, stop, load state, continue. The framework just does the bookkeeping.

### The Claude Agent SDK

The Claude Agent SDK (`pip install claude-agent-sdk`) takes a different approach: it gives you the **same agent that powers Claude Code** as a library. Instead of defining a graph, you give it a task, a set of allowed tools and a permission mode, and it runs a capable general-purpose agent with built-in tools for reading and editing files, running commands and searching the web, plus hooks, subagents, MCP servers and sessions.

```python
import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, query


async def main():
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Glob"], permission_mode="acceptEdits"),
    ):
        if isinstance(message, ResultMessage):
            print("Done:", message.subtype)

asyncio.run(main())
```

It suits agents that work on files and code, or that need a strong general agent loop with permissions and hooks, without you designing the control flow. LangGraph suits workflows where **you** want explicit control over the steps.

Other names you'll meet: the **OpenAI Agents SDK**, **CrewAI** (role-based multi-agent teams), **Pydantic AI** (type-safe agents built on Pydantic), **LlamaIndex** (strong on RAG-heavy agents). The concepts in this section transfer to all of them.

## 4. The costs

Frameworks aren't free:

- **Abstraction.** The model call is buried several layers deep. When the agent misbehaves, the question "what exact messages did we send?" can be hard to answer without the framework's tracing tool.
- **Debugging.** Stack traces run through framework internals. Errors appear far from their cause, for example a state key typo that surfaces three nodes later.
- **Churn.** Agent frameworks change fast; APIs get renamed and deprecated between minor versions. Code and tutorials from a year ago may not run.
- **Lag behind the API.** New model features (a new stop reason, a new tool type, new parameters) reach the raw SDK first. A framework wrapper may not expose them for weeks.
- **Weight.** More dependencies, more to learn, more to keep updated, sometimes vendor-specific hosting or tracing services.
- **Hidden behaviour.** Default retry policies, prompt templates and history handling you didn't choose and may not notice.

## 5. When to use one, and when not

Use **your own loop** when:

- The agent is a single loop with a handful of tools (most agents).
- You need precise control over prompts, approvals, logging and cost.
- You want the fewest moving parts to debug and deploy.
- You're learning, or the client's team will maintain the code and doesn't know the framework.

Use **a framework** when:

- The control flow is a real graph: several stages, branches, loops, sub-agents, parallel steps.
- You need durable pauses and resumes (long human approvals, runs that survive deploys) and don't want to build checkpointing yourself.
- You'll benefit from its tracing UI across a team.
- The client already uses it, or the job asks for it.
- For the Claude Agent SDK specifically: the agent's job is working with files, code or a shell, which its built-in tools already do well.

A practical path: write the loop yourself, as in *A production-grade tool loop*, and move to a framework only when you find yourself rebuilding checkpointing, interrupts or a graph engine. Because you understand the parts, switching later is straightforward, and you'll be able to read the framework's traces with real understanding.

> **Try it:** In the practice editor, build the tiny `Graph` and run the draft–review loop with checkpoints. Print each checkpoint: that list is what a framework's trace view shows you.

## Common mistakes

- **Starting with a framework before you can write the loop.** You can't debug what you don't understand.
- **Choosing a framework for a two-step workflow.** Plain functions are clearer.
- **Copying old tutorial code** for a fast-moving library without checking the current docs.
- **Ignoring the framework's defaults** for retries, history and prompts.
- **No turn or step limit** on graphs with cycles.
- **Mixing state styles**: some data in the graph state, some in globals, so resume restores only half of it.

## Recap

- Frameworks package the loop, tools, graph-based control flow, typed state, checkpoints, human-in-the-loop interrupts and tracing.
- LangGraph models an agent as a `StateGraph`: nodes return state updates, edges (some conditional) pick the next node, a checkpointer saves state per `thread_id`, and `interrupt()` / `Command(resume=...)` pause for humans.
- The Claude Agent SDK gives you Claude Code's agent loop and built-in tools as a library.
- The costs are abstraction, harder debugging, churn and lag behind the raw API.
- Default to your own loop; adopt a framework when you'd otherwise rebuild its graph, checkpoint or interrupt machinery.
