# What agents are, and when you need one

## Why this matters

"Build us an AI agent" is one of the most common requests you'll see for AI work right now, and many of those projects fail because an agent was the wrong tool. An engineer who can say "this should be a two-step workflow, not an agent, and here's why" ships faster, spends less, and builds something that works on Monday morning. This lesson gives you the vocabulary and the judgement; the rest of the section gives you the code.

## 1. Workflows versus agents

In *Tool calling* you wrote a loop: call the model, run the tools it asks for, send back the results, repeat until it says it's done. That loop is the seed of everything here. What matters is **who decides the next step**.

- A **workflow** is a system where LLM calls and tools follow **paths you wrote in code**. The model fills in the blanks (summarise this, classify that), but the sequence is fixed.
- An **agent** is a system where the **model decides** which tools to use, in what order, and when it's finished. Your code provides the tools and the loop; the model steers.

Anthropic's article *Building effective agents* draws exactly this line, and its central advice is blunt: find the simplest solution that works, and only add complexity when it clearly improves results. Many "agents" in production are really workflows, and that's a compliment.

Here's the same task done both ways. The job: answer a customer question about an order.

```python
# Workflow: the path is fixed in code.
def answer_order_question(client, order_id: str, question: str) -> str:
    order = db.get_order(order_id)                  # step 1: always look up the order
    policy = search_policies(question)              # step 2: always retrieve policy text
    response = client.messages.create(              # step 3: one LLM call to write the answer
        model="claude-opus-5-5", max_tokens=2000,
        messages=[{"role": "user", "content":
            f"<order>{order}</order>\n<policy>{policy}</policy>\n<question>{question}</question>"}],
    )
    return response.content[0].text
```

```python
# Agent: the model chooses which tools to call and when to stop.
result = run_agent(client, task=question,
                   tools=[get_order_tool, search_orders_tool, search_policies_tool, get_tracking_tool],
                   handlers=HANDLERS, max_turns=8)
```

The workflow is cheaper, faster, easier to test, and wrong whenever the question needs something you didn't anticipate ("I have two orders, which one shipped?"). The agent handles open-ended questions but costs more per request, is slower, and can go wrong in more ways.

## 2. When is an agent worth it?

Ask four questions before you reach for an agent:

1. **Complexity.** Is the path to the answer genuinely unpredictable? If you can draw the flowchart, write the flowchart. Agents earn their keep when the number of steps and their order depend on what the agent finds along the way: debugging code, researching a topic, handling messy support tickets.
2. **Value.** Is a correct result worth the cost? An agent might make 10–30 model calls for one task. At Opus 5.5 prices ($4 input / $20 output per million tokens), a run that sends 20 calls averaging 8,000 input and 500 output tokens costs about `20 × (8000 × 4 + 500 × 20) / 1,000,000 ≈ $0.84`. Fine for a sales lead worth $500; ridiculous for routing an email.
3. **Viability.** Can the model actually do each step well? Test the hardest single step on its own first. If Claude can't reliably read your invoice format in one call, an agent that reads fifty of them won't do better.
4. **Cost of errors, and whether they're catchable.** What happens when the agent is wrong? A wrong draft that a human reviews is cheap. A wrong refund, deleted record or email to a customer is not. Agents suit tasks where mistakes can be **detected and fixed**: code that tests can check, drafts a person approves, research a reader verifies.

> **Note:** Coding agents work well partly because code is verifiable: tests pass or fail. Look for that property in any agent task you take on. If nothing can check the agent's work, you need a human to.

## 3. The anatomy of an agent

Every agent, from a 40-line script to a commercial product, has the same five parts:

| Part | What it is | In your code |
|---|---|---|
| **Model** | The LLM that decides what to do next | `client.messages.create(model=...)` |
| **Tools** | Functions the model can ask you to run | `tools=[...]` plus handler functions |
| **Loop** | Call, run tools, feed results back, repeat | `for turn in range(max_turns): ...` |
| **Memory** | What the agent knows: the message history, plus any saved facts | `messages` list, a database |
| **Stop condition** | When to finish: model says done, budget hit, human says stop | `stop_reason`, `max_turns`, cost limit |

Each of the next lessons strengthens one part: *A production-grade tool loop* hardens the loop and tools, *Memory and state* covers memory, *Humans in the loop* adds safe stop conditions and approvals, and *Evals: measuring LLM features and agents* tells you whether the whole thing works.

Here's a minimal agent, all five parts visible:

```python
import anthropic

client = anthropic.Anthropic()

TOOLS = [{
    "name": "search_docs",
    "description": "Search the product docs. Returns the 3 most relevant passages.",
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"], "additionalProperties": False},
}]


def search_docs(query: str) -> str:
    return "Refunds are issued within 5 business days of approval."   # stub


messages = [{"role": "user", "content": "How long do refunds take?"}]       # memory
for turn in range(5):                                                       # loop + stop condition
    response = client.messages.create(model="claude-opus-5-5",              # model
                                      max_tokens=4000, tools=TOOLS, messages=messages)
    if response.stop_reason != "tool_use":                                  # stop condition
        print(response.content[-1].text)
        break
    messages.append({"role": "assistant", "content": response.content})
    results = [{"type": "tool_result", "tool_use_id": b.id, "content": search_docs(**b.input)}  # tools
               for b in response.content if b.type == "tool_use"]
    messages.append({"role": "user", "content": results})
```

## 4. Five workflow patterns

Before building a full agent, check whether one of these patterns (named in *Building effective agents*) does the job. They're simple to build, easy to test, and cover most real requests.

### Prompt chaining

Split a task into fixed steps, each LLM call working on the previous one's output, with **gates**: plain code checks between steps that stop early if something's off.

```python
outline = call(client, f"<topic>{topic}</topic> Write a bullet outline.")
if outline.count("\n- ") < 2:                          # gate: cheap code check
    raise ValueError("outline too thin")
draft = call(client, f"<outline>{outline}</outline> Write the article.")
```

Use it when the task splits cleanly into steps and each step is easier than the whole. The gate is the important part: a bad intermediate result stops the chain before you pay for the next call.

### Routing

Classify the input, then send it to a specialised prompt, tool set or model. A cheap model can classify; an expensive one answers only the hard cases.

```python
category = classify(client, message, model="claude-haiku-5-5")   # billing / technical / general
answer = call(client, message, system=SPECIALIST_PROMPTS[category], model="claude-opus-5-5")
```

Use it when inputs fall into distinct groups that need different handling. Routing also saves money: Haiku 5.5 costs $0.10 / $0.50 per million tokens, 40 times cheaper than Opus.

### Parallelisation

Run independent LLM calls at the same time and combine the results. Two flavours:

- **Sectioning:** split one job into independent parts (review a contract's payment terms, liability clause and termination clause separately).
- **Voting:** run the same task several times and combine (three independent "is this code vulnerable?" checks, flag if any says yes).

```python
import asyncio

async def review(client, contract: str) -> list[str]:
    aspects = ["payment terms", "liability", "termination"]
    tasks = [ask(client, f"Review only the {a} in <contract>{contract}</contract>") for a in aspects]
    return await asyncio.gather(*tasks)
```

You built the tools for this in *Async Python*: `asyncio.gather` with a `Semaphore` to limit concurrency.

### Orchestrator–workers

A central LLM breaks a task into subtasks **it decides on at run time**, hands each to a worker call, and combines the results. The difference from parallelisation: the subtasks aren't known in advance.

```python
plan = parse_plan(client, task)            # orchestrator returns e.g. ["check pricing page", "check docs", ...]
results = [worker(client, subtask) for subtask in plan.subtasks]
report = synthesise(client, task, results)
```

Use it for research ("compare these three vendors") or multi-file code changes, where the work depends on the input.

### Evaluator–optimiser

One call produces an answer; another evaluates it against criteria and gives feedback; repeat until it passes or you hit a limit.

```python
draft = write(client, brief)
for _ in range(3):
    review = evaluate(client, draft, criteria)    # structured: {"passed": bool, "feedback": str}
    if review.passed:
        break
    draft = write(client, brief, feedback=review.feedback, previous=draft)
```

Use it when there are clear evaluation criteria and iteration measurably helps, such as translation, or writing that must hit specific requirements. Always cap the iterations.

> **Try it:** In the practice editor, build the prompt chain with a gate. Notice how the gate makes the failure cheap: one call instead of two.

## 5. Start simple

The order to try things in:

1. **One well-prompted LLM call**, with retrieval or examples in the prompt. This solves more than people expect.
2. **A workflow** from the patterns above.
3. **An agent**, only when the steps truly can't be known in advance.

And when you do build an agent:

- **Keep the tool set small and clear.** Five well-described tools beat twenty overlapping ones. The model picks tools from their descriptions, so a vague description means wrong choices.
- **Make the agent's progress visible.** Log every tool call and result (you'll do this in the next lesson). You can't debug what you can't see.
- **Put limits everywhere**: turns, tokens, money, time.
- **Measure.** Build a small eval set before you start tweaking prompts, or you won't know whether a change helped (covered in *Evals: measuring LLM features and agents*).

Frameworks can hide these parts behind abstractions. Write the loop yourself first, as this section does, so you understand what a framework is doing when you use one later.

## Common mistakes

- **Building an agent for a fixed process.** If you can write the steps down, write them as code.
- **Skipping the viability test.** Check the hardest single step works in one call before you wrap a loop around it.
- **No stop condition but the model's own.** Always add a turn limit and a cost limit.
- **Agents with irreversible actions and no review step.** If a mistake can't be caught, a human must approve before it happens.
- **Too many tools, poorly described.** The model can only choose well between tools it can tell apart.
- **Judging an agent by a few demos.** It works on the three examples you tried; measure it on fifty.

## Recap

- A **workflow** follows code paths you wrote; an **agent** lets the model choose its own steps.
- Use an agent when the task is complex and unpredictable, valuable enough to pay for many calls, viable step by step, and its errors are catchable.
- Every agent is a model, tools, a loop, memory and a stop condition.
- Try prompt chaining, routing, parallelisation, orchestrator–workers and evaluator–optimiser before a full agent.
- Start with the simplest thing that works, add complexity only when measurements say it helps.
