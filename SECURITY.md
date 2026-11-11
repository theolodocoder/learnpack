# Security

LearnPack runs learners' code on their own computer. That's what makes the exercises real, and it's why the security model matters.

## What the app protects against

- **Other websites using it to run code on your machine.** The server listens only on `127.0.0.1`. Every API call needs a random token created at each launch, and the `Host` header must be `localhost` or `127.0.0.1`. That blocks cross-site requests and DNS-rebinding attacks.
- **Script injection from course content.** Lesson Markdown is sanitised with DOMPurify before it's shown.
- **Path tricks in packs or requests.** Ids must match `^[a-z0-9][a-z0-9-]{0,63}$`, and file references must stay inside the pack.
- **Learners seeing the answers by accident.** Hidden tests and solutions are never sent to the browser unless the learner clicks **Show solution**.

## What it does not protect against

- **Malicious course packs.** A pack's exercises and their tests run as real Python or Node code with your user's permissions. **Only install packs from people you trust**, the same way you'd treat any script you download.
- **Code you write and run yourself.** Exercises are not sandboxed beyond a 60-second time limit.

## API keys

Keys go in `.env` in the LearnPack folder. That file is git-ignored and passed only to exercise processes when you click **Run**. **Check** never needs a key.

## Reporting a vulnerability

Please don't open a public issue. Use GitHub's **[Report a vulnerability](https://github.com/theolodocoder/learnpack/security/advisories/new)** (private advisory) on this repository, with steps to reproduce. You'll get a reply within a week.
