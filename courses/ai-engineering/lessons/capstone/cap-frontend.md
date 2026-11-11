# A usable frontend, fast

## Why this matters

Users don't see your backend. They see a page, or a chat, and they decide in ten seconds whether it works. A capstone with a great RAG pipeline behind a confusing page will get worse feedback than a simpler one behind a clear page. You don't need to become a frontend engineer. You need a frontend that streams answers, shows when it's working, explains errors in plain words, accepts a file, and is usable with a keyboard and a screen reader. That's what this lesson covers.

## 1. Choose the right kind of frontend

| Option | Best for | Strengths | Limits |
|---|---|---|---|
| **Streamlit** | Internal tools, admin pages, demos to one business | Pure Python; a chat UI in ~30 lines; free hosting on Streamlit Community Cloud | Looks like Streamlit; reruns the whole script on every interaction; weak for public, branded products |
| **Plain HTML + JavaScript** | A small public page served by your FastAPI app | No build step; one file; fast; full control | You write the DOM updates yourself |
| **Next.js** | Public products that need to look and feel like real apps | React components, routing, great hosting on Vercel, the industry standard | A new language and toolchain to learn; more moving parts |
| **No web UI** (WhatsApp, Telegram, email) | Users who live in messaging apps | Nothing to install or learn for the user | Covered in *Messaging channels* |

A sensible capstone choice:

- The **shop bot**: users are on WhatsApp, so no customer-facing web UI at all. The owner gets a small **Streamlit** admin page (conversations, thumbs up/down, editing the price list).
- The **job assistant**: a public **Next.js** or **plain HTML** page where students paste a job post and upload a CV.
- **Meeting notes**: a **Streamlit** app is fine if your users are one team; Next.js if you want strangers to sign up.

Whatever you pick, the frontend never holds your Anthropic key. It talks to *your* FastAPI backend, which holds the key, the prompts and the rate limits.

> **Note:** Streamlit and Next.js aren't installed in this practice environment, so their code below is for reading, not running here. Install them in your capstone repo (`pip install streamlit`; `npx create-next-app@latest`).

## 2. Streamlit: a chat UI in Python

Streamlit runs your script top to bottom on every interaction. `st.session_state` is a dict that survives those reruns, so it holds the chat history. The chat elements `st.chat_message` and `st.chat_input` give you a familiar chat layout, and `st.write_stream` displays a generator's chunks as they arrive and returns the full text.

```python
# app.py  (run with: streamlit run app.py)
import httpx
import streamlit as st

from client import stream_answer   # the generator you write in this lesson's exercise

API_URL = st.secrets.get("API_URL", "http://localhost:8000")
st.title("Kemi's Fashion: assistant preview")

if "history" not in st.session_state:
    st.session_state.history = []          # [{"role": "user"|"assistant", "content": str}]

for msg in st.session_state.history:      # redraw the conversation on every rerun
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask about a product, price or delivery"):
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        try:
            with httpx.Client(base_url=API_URL, timeout=60) as client:
                answer = st.write_stream(stream_answer(client, question))
        except (httpx.HTTPError, RuntimeError):
            answer = "Sorry, something went wrong. Please try again in a minute."
            st.error(answer)
    st.session_state.history.append({"role": "assistant", "content": answer})
```

Each piece maps to a real need: history in session state, the chat layout, streaming with `st.write_stream`, and a plain-language error with `st.error`. For uploads, `st.file_uploader("Upload your CV", type=["pdf", "docx", "txt"])` returns a file-like object (or `None`) you can send on to the backend.

## 3. Talking to the backend: streaming over SSE

Your backend from *Serving Claude from FastAPI* streams server-sent events from `POST /chat/stream`:

```
data: {"text": "Yes, we "}

data: {"text": "deliver to Ibadan."}

data: [DONE]

```

On the Python side (Streamlit, a CLI, or a test), `httpx` can read that as it arrives. `client.stream(...)` opens the response without downloading it all, and `response.iter_lines()` yields one line at a time:

```python
import json
import httpx

def handler(request):   # a fake backend, so this runs offline
    body = b'data: {"text": "Yes, we "}\n\ndata: {"text": "deliver."}\n\ndata: [DONE]\n\n'
    return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})

client = httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(handler))
with client.stream("POST", "/chat/stream", json={"message": "Ibadan?"}) as response:
    for line in response.iter_lines():
        if line.startswith("data: ") and line != "data: [DONE]":
            print(json.loads(line[6:])["text"], end="")
# Yes, we deliver.
```

The exercise turns this into a proper generator that stops at `[DONE]` and raises on `error` events and bad status codes.

On a web page, the browser's `fetch` gives you the same stream. Here's a complete minimal page you can serve from FastAPI. It's plain HTML and JavaScript with no build step:

```html
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job post helper</title></head>
<body>
<main>
  <h1>Job post helper</h1>
  <form id="ask">
    <label for="q">Paste a job post</label>
    <textarea id="q" name="q" rows="8" required maxlength="8000"></textarea>
    <button type="submit">Tailor my CV</button>
  </form>
  <p id="status" role="status" aria-live="polite"></p>
  <div id="answer" aria-live="polite"></div>
</main>
<script>
const form = document.getElementById("ask"), out = document.getElementById("answer"),
      status = document.getElementById("status"), button = form.querySelector("button");
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  out.textContent = ""; status.textContent = "Working on it…"; button.disabled = true;
  try {
    const res = await fetch("/chat/stream", {method: "POST", headers: {"Content-Type": "application/json"},
                                             body: JSON.stringify({message: form.q.value})});
    if (res.status === 429) throw new Error("You've sent a lot of requests. Please wait a minute.");
    if (!res.ok) throw new Error("The service is having trouble. Please try again shortly.");
    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = "";
    while (true) {
      const {value, done} = await reader.read();
      if (done) break;
      buffer += value;
      const events = buffer.split("\n\n"); buffer = events.pop();   // keep a partial event for later
      for (const ev of events) {
        const data = ev.replace(/^data: /, "");
        if (data === "[DONE]") continue;
        const msg = JSON.parse(data);
        if (msg.error) throw new Error(msg.error);
        out.textContent += msg.text;            // textContent, never innerHTML: no injected HTML
      }
    }
    status.textContent = "Done.";
  } catch (err) {
    status.textContent = err.message;
  } finally {
    button.disabled = false;
  }
});
</script>
</body>
</html>
```

Serve it from the same FastAPI app (`app.mount("/", StaticFiles(directory="static", html=True))`, added *after* your API routes) and you avoid cross-origin issues entirely. If the frontend lives on another domain (a Next.js app on Vercel calling an API on Render, say), add FastAPI's `CORSMiddleware` with `allow_origins` set to that exact domain, never `"*"` with credentials.

> **Note:** The browser's built-in `EventSource` only supports `GET` requests, which is why the page above reads the `fetch` body directly for a `POST`.

## 4. Next.js, briefly

For a public product, Next.js is the common choice. With the App Router, a page is a React component in `app/page.tsx`; interactive parts are marked `"use client"`. The streaming logic is the same `fetch` loop as above, with React state instead of `textContent`:

```tsx
"use client";
import { useState } from "react";

export default function Page() {
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  async function ask(formData: FormData) {
    setAnswer(""); setStatus("loading");
    const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/chat/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: formData.get("q") }),
    });
    if (!res.ok || !res.body) { setStatus("error"); return; }
    // ...same reader loop as the HTML page, calling setAnswer(a => a + msg.text)
    setStatus("idle");
  }

  return (
    <form action={ask}>
      <label htmlFor="q">Paste a job post</label>
      <textarea id="q" name="q" required />
      <button disabled={status === "loading"}>{status === "loading" ? "Working…" : "Tailor my CV"}</button>
      {status === "error" && <p role="alert">Something went wrong. Please try again.</p>}
      <div aria-live="polite">{answer}</div>
    </form>
  );
}
```

Anything prefixed `NEXT_PUBLIC_` is shipped to the browser, so only put your *backend's URL* there, never a secret key. Deploy to Vercel by connecting the GitHub repo. If Next.js is new to you, don't learn it during the capstone unless your product truly needs a public, branded app: the plain HTML page above gets you 80% of the way in an afternoon.

## 5. Loading, empty and error states

Every screen that waits on an LLM has at least four states. Design each one deliberately:

| State | What the user should see |
|---|---|
| **Empty** (first visit) | What this does, in one sentence, and an example to click: "Try: *Do you deliver to Abuja?*" |
| **Loading** | Immediate feedback: a disabled button and "Working on it…". With streaming, the first words should arrive within a second or two. |
| **Success** | The answer, plus a way to give feedback (👍 / 👎) and to copy it. |
| **Error** | Plain words and a next step: "The service is busy. Please try again in a minute." Never a stack trace or a raw provider error. |

Map backend responses to messages once, in one place: 429 → "slow down", 503 → "busy, try again", 502/504 → "having trouble", network error → "check your connection". Nigerian mobile connections drop often; a "try again" button that resends the last message is worth adding.

## 6. File upload

The job assistant needs a CV; the meeting tool needs a transcript. On the backend, FastAPI receives files with `UploadFile` (this needs the `python-multipart` package installed in your project):

```python
from fastapi import FastAPI, HTTPException, UploadFile

app = FastAPI()
MAX_BYTES = 2 * 1024 * 1024
ALLOWED = {"text/plain", "text/markdown", "application/pdf"}

@app.post("/cv")
async def upload_cv(file: UploadFile):
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Please upload a PDF, .txt or .md file.")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "That file is over 2 MB.")
    # extract text (pypdf for PDFs), store it, return an id
    return {"filename": file.filename, "bytes": len(data)}
```

On the page, `<input type="file" accept=".pdf,.txt,.md">` inside a form, sent with `fetch("/cv", {method: "POST", body: new FormData(form)})` (don't set `Content-Type` yourself; the browser adds the multipart boundary). Validate type and size on the server even if the page checks too: the browser check is a convenience, the server check is the security.

## 7. Basic accessibility

Accessibility is part of "usable", and most of it is free if you use the right HTML elements:

- **Label every input.** `<label for="q">` linked to `id="q"`. A placeholder is not a label: it disappears when you type and many screen readers skip it.
- **Use real buttons and forms.** `<button>` inside `<form>` works with Enter, Tab and screen readers. A clickable `<div>` doesn't.
- **Announce changes.** Streaming text and status messages should be in an `aria-live="polite"` region (or `role="status"`), so screen-reader users hear that something happened. Use `role="alert"` for errors.
- **Keep keyboard focus visible.** Don't remove the focus outline with CSS. After an answer arrives, focus should still be somewhere sensible.
- **Contrast and size.** Text at least 16px; dark enough on its background (WCAG asks for a 4.5:1 contrast ratio for normal text).
- **Language and layout.** `<html lang="en">`, a viewport meta tag, and a layout that works on a small Android phone, because that's what most of your users will hold.

Streamlit and Next.js get many of these right by default; your job is mainly to write labels and meaningful error text.

## Common mistakes

- **Putting the API key in the frontend.** Including in `NEXT_PUBLIC_` variables. The browser can read everything you send it.
- **No loading state.** Users click three times and you pay for three answers.
- **Not streaming.** A 15-second blank wait feels broken; the same answer streamed feels fast.
- **Raw errors on screen.** Map them to plain words with a next step.
- **`innerHTML` with model output.** Use `textContent`, or render Markdown with a sanitiser. Model output is untrusted input.
- **Trusting the browser's file checks.** Check type and size on the server.
- **Learning a framework during the capstone when you don't need it.** Pick the simplest frontend your users will accept.

## Recap

- Streamlit for internal tools and quick demos; plain HTML or Next.js for public products; no web UI if users live in WhatsApp.
- The frontend talks only to your backend, which holds the key.
- Stream with SSE: `httpx` `client.stream` + `iter_lines()` in Python, a `fetch` body reader in the browser.
- Design the empty, loading, success and error states on purpose.
- Upload with `UploadFile`; validate type and size on the server.
- Labels, real buttons, `aria-live` regions, visible focus and good contrast cover most accessibility basics.
