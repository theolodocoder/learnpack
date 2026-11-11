# Prompt engineering for developers

## Why this matters

The prompt is the code that runs inside the model. A vague prompt gives vague, inconsistent output, and no amount of Python around it will fix that. A clear prompt with the right context and examples often turns a "this model can't do it" task into one that works reliably on the cheapest model. Prompt engineering for developers isn't about magic phrases: it's writing precise specifications, keeping them in version-controlled functions, and testing them against real inputs like any other code.

## 1. Be clear and specific

Imagine handing the task to a smart new colleague who knows nothing about your project. What would they need to know? The model is in the same position: it has broad knowledge but zero context about **your** situation.

Vague:

```
Summarise this email.
```

Specific:

```
Summarise the customer email below for a support agent who will reply to it.
- Start with one sentence stating what the customer wants.
- Then list any order numbers, dates and amounts mentioned.
- Flag if the customer threatens to cancel or mentions a chargeback.
- At most 80 words. No greeting, no sign-off.
```

The second version says **who** the output is for, **what** to include, **what format**, and **how long**. Each of those is a decision the model would otherwise make for you, differently each time.

Current Claude models follow instructions precisely. That's good, but it means they do what you **say**, not what you meant. If you want the model to go beyond the literal request ("suggest improvements as well as fixing the bug"), ask for it.

Some habits that help:

- **Say what to do, not only what to avoid.** "Write in flowing paragraphs" works better than "don't use bullet points".
- **Number the steps** when order matters.
- **Define the output format** exactly when a program will read it.
- **Say what to do when the answer is unknown**: "If the email doesn't mention an order number, write `none`." Otherwise the model may guess.

## 2. Give context and the "why"

Explaining the reason behind an instruction lets the model generalise to cases you didn't foresee.

```
NEVER use abbreviations.
```

versus

```
Your answer will be read aloud by a text-to-speech system, so write out
abbreviations in full ("for example", not "e.g.") and avoid symbols it can't pronounce.
```

With the reason, the model also avoids things you didn't list (emoji, URLs, tables) because it understands the goal.

Useful context to include:

- Who the users are and what they're trying to do.
- What happens to the output next (shown in a UI, parsed by code, emailed to a customer).
- What "good" looks like, and common failure cases you've seen.
- Domain facts the model can't know: your product names, policies, prices.

## 3. Role prompts

A one-line role in the system prompt sets the expertise and tone:

```python
system = "You are a senior Python reviewer at a fintech company. You care about correctness and security first, style second."
```

Roles are a cheap, useful nudge, but they're not a substitute for specific instructions. "You are an expert copywriter" plus a vague task still gives vague output. Combine a role with the details from sections 1 and 2.

## 4. Use XML tags to separate data from instructions

When a prompt mixes instructions with data (an email, a document, a user's question, examples), wrap each kind in its own XML-style tags:

```python
email = "Hi, I was charged twice for order #4471 on 3 Nov. Fix this or I'm cancelling. – Tunde"

prompt = f"""<email>
{email}
</email>

Summarise the email above for a support agent. State what the customer wants in one
sentence, then list any order numbers and dates. Put your summary in <summary> tags."""
```

Why tags help:

- **No ambiguity.** The model can tell exactly where the email ends and your instructions begin, even if the email itself contains instructions-like text ("ignore the previous message…").
- **Easy to reference.** "the email in `<email>` tags" is unambiguous.
- **Easy to parse output.** Ask for the answer in `<summary>` tags and extract it with a regex, ignoring any preamble.

```python
import re

def extract_tag(text: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else None

print(extract_tag("Sure! <summary>Double charge on #4471.</summary>", "summary"))
# Double charge on #4471.
```

There are no special tag names: `<document>`, `<email>`, `<contract>` all work. Pick descriptive names and use them consistently. For several documents, nest them:

```
<documents>
<document index="1">
<source>q3_report.pdf</source>
<content>...</content>
</document>
...
</documents>
```

> **Note:** For long documents (thousands of tokens), put the documents **at the top** of the prompt and your instructions and question **at the end**. This ordering measurably improves answer quality on long inputs.

## 5. Show examples (few-shot prompting)

One of the most reliable ways to get a specific format or style is to show it. A prompt with examples is called **few-shot**; without, **zero-shot**.

```python
EXAMPLES = """<examples>
<example>
<input>Arrived in two days, works perfectly.</input>
<output>positive</output>
</example>
<example>
<input>Screen cracked within a week. Seller ignored me.</input>
<output>negative</output>
</example>
<example>
<input>It's a phone case. It fits the phone.</input>
<output>neutral</output>
</example>
</examples>"""

def sentiment_prompt(review: str) -> str:
    return f"""Classify the sentiment of a product review as positive, negative or neutral.

{EXAMPLES}

<review>
{review}
</review>

Answer with the label only, inside <label></label> tags."""
```

Make examples:

- **Relevant**: they look like your real inputs, not toy ones.
- **Diverse**: cover the edge cases (the "neutral" example above stops the model treating every non-complaint as positive).
- **Clearly marked**: in `<example>` tags so they aren't confused with the real task.

Three to five good examples usually beat a page of instructions. Be aware the model copies examples closely: if all your examples are short, outputs will be short.

Since you control `messages`, examples can also be written as fake earlier turns (a user message and the "assistant" reply you want). Both styles work; tags in one prompt are simpler to build and test.

## 6. Ask for reasoning before the answer

The model writes left to right and can't revise. For anything that needs thought (maths, multi-step logic, judging a contract clause), asking it to reason **first** gives it room to work, and the reasoning tokens become context for the final answer.

```python
prompt = f"""<contract>
{contract_text}
</contract>

Does this contract allow either party to terminate without cause?
First, think through the relevant clauses inside <thinking> tags.
Then give your answer, yes or no, inside <answer> tags, followed by the clause number."""
```

You parse out `<answer>` and ignore (or log) `<thinking>`. The reasoning costs output tokens, so use it where accuracy matters, not for simple lookups.

### Adaptive thinking and `effort` on current models

Current Claude models can also **think internally** before answering. This is called *adaptive thinking*: the model decides how much to think based on how hard the request is, and the thinking appears as `thinking` blocks in `response.content` (another reason to filter blocks by `type`). Thinking tokens are billed as output tokens.

You steer how much effort it spends with the `effort` setting:

```python
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    output_config={"effort": "low"},   # "low" | "medium" | "high" | "xhigh" | "max"
    messages=[{"role": "user", "content": "Classify: 'Refund please' -> billing or bug?"}],
)
```

Lower effort is faster and cheaper (good for classification and simple extraction); higher effort is better for hard reasoning and agentic work. Asking for explicit `<thinking>` in your prompt still works and has one advantage: you can read and log the reasoning in your own format.

> **Note:** Older models had a `temperature` knob and supported "prefilling" the start of the assistant's reply. Neither works on current models (the API rejects them), so control format with instructions, tags, examples and structured output instead.

## 7. Prompts are code: write them as functions

Don't scatter f-strings across your app. Put each prompt in a function with typed parameters:

```python
def build_review_prompt(code: str, language: str, focus: list[str]) -> str:
    focus_list = "\n".join(f"- {f}" for f in focus)
    return f"""<code language="{language}">
{code}
</code>

Review the code above. Focus on:
{focus_list}

For each problem, give the line number, the issue, and a fix.
If there are no problems in an area, say so in one line."""
```

Benefits:

- One place to change the wording; every caller gets the update.
- **Unit-testable** without calling the API: check that the data is inside its tags, that inputs are validated, that nothing is duplicated.
- Version control shows exactly how the prompt changed and when quality changed with it.

Validate inputs in the function, the same as any other code: an empty document or a negative word limit should raise `ValueError` before you spend money on an API call.

## 8. Iterate against test inputs

Prompt engineering is an experimental loop:

1. Write down what "good" means for this task (ideally as something you can check in code).
2. Collect a handful of **real** test inputs, including awkward ones: empty, very long, ambiguous, in another language, containing instructions.
3. Run the prompt on all of them.
4. Look at the failures, change **one thing**, and run again.

Even a tiny harness beats eyeballing one output:

```python
CASES = [
    ("Arrived fast, love it.", "positive"),
    ("Broke after two days.", "negative"),
    ("It's blue.", "neutral"),
    ("Great, another charger that doesn't charge.", "negative"),  # sarcasm
]

def accuracy(classify) -> float:
    results = [(text, want, classify(text)) for text, want in CASES]
    for text, want, got in results:
        if got != want:
            print(f"MISS: {text!r} expected {want}, got {got}")
    return sum(want == got for _, want, got in results) / len(results)
```

Re-run it every time you touch the prompt or switch models. This is the seed of **evals**, which get a full section later; for now, the habit matters more than the tooling.

## Common mistakes

- **Vague instructions** ("make it better", "summarise") with no audience, format or length.
- **Mixing data and instructions** with no separation, so the model can't tell which is which, and a malicious document can hijack your prompt.
- **Only negative instructions** ("don't…") without saying what to do instead.
- **Examples that are all alike**, so the model overfits to their length or style.
- **Testing on one input** and declaring victory.
- **Changing several things at once** while iterating, so you can't tell what helped.
- **Building prompts with ad-hoc string concatenation** throughout the codebase instead of tested functions.
- **Reaching for removed knobs** like `temperature` or prefill on current models.

## Recap

- Write prompts like specs: audience, task, format, length, what to do when unsure.
- Explain **why**; the model generalises from reasons.
- Use a role for tone and expertise, plus specific instructions.
- Wrap data in XML tags; put long documents first and the question last; ask for answers in tags you can parse.
- Show 3–5 relevant, diverse examples.
- Ask for reasoning before the answer on hard tasks; current models also think adaptively, steered with `output_config={"effort": ...}`.
- Keep prompts in tested Python functions and iterate against a fixed set of real test inputs.
