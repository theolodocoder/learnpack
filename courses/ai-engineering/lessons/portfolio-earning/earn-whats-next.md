# What's next: the deep dive, while you keep earning

## Why this matters

You can now build, ship, evaluate and sell LLM products. That's a real, employable skill set. But so far you've mostly used models as a black box behind an API. The engineers who grow fastest over the next few years understand what's inside the box: how a transformer is trained, why it fails the way it does, and how inference is made fast and cheap. That understanding makes you better at the applied work (debugging, choosing models, reading papers, fine-tuning when it actually helps) and it opens doors to more senior and research-adjacent roles. This lesson is the plan for 2027, and how to do it without stopping the income you've started.

## 1. The order matters

The deep-dive path, in order:

1. **Andrej Karpathy, *Neural Networks: Zero to Hero***
2. **Probability and statistics**
3. **Classic machine learning**
4. **PyTorch and Hugging Face**
5. **Stanford CS336: Language Modeling from Scratch**
6. **Inference: vLLM, quantisation, KV cache**

Each step uses the one before it. Karpathy gives you the core intuition by building things; probability and classic ML fill in the theory you'll need to read papers and evaluate models properly; PyTorch and Hugging Face are the practical tools; CS336 goes deep on training language models; inference closes the loop back to the production systems you already build.

## 2. Karpathy: Neural Networks, Zero to Hero

The single best resource on the list. Karpathy builds everything from scratch in code, step by step:

- **micrograd**: a tiny autograd engine. You implement backpropagation yourself, which turns the chain rule you met in the maths section into working code.
- **makemore**: character-level language models, from bigram counts to an MLP to more modern architectures, including the training tricks (initialisation, batch normalisation) and how to diagnose training.
- **Let's build GPT**: a transformer language model from an empty file, with self-attention implemented by hand.
- **Tokenizer**: building a byte-pair-encoding tokenizer, which explains a lot of strange LLM behaviour (why models struggle to count letters, why some languages cost more tokens).

How to study it:

- **Type every line yourself.** Don't copy. Pause, predict what the next line does, then write it.
- **Re-derive one thing per video from memory** the next day.
- **Change something and measure it**: a different learning rate, a bigger context, a different tokenizer vocabulary. Write down what happened.
- **Post about it.** "I built backprop from scratch; here's the 40-line version" is excellent build-in-public content and shows depth to future interviewers.

Budget a few weeks per major video if you do it alongside client work. It's fine to be slow; it's not fine to skip the coding.

## 3. Probability and statistics

You'll need probability to understand sampling, likelihoods, cross-entropy loss, and to evaluate models honestly: confidence intervals on eval scores, whether an improvement from 0.84 to 0.87 on 60 questions is real or noise, A/B tests on features.

Steve Brunton's *Probability Bootcamp* (on his YouTube channel) is a good structured route. Focus on: random variables and distributions, expectation and variance, conditional probability and Bayes' rule, the law of large numbers and central limit theorem, maximum likelihood, and basic hypothesis testing.

A small example of why it matters to you right now:

```python
import math

def accuracy_interval(correct: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Approximate 95% confidence interval for an accuracy score (normal approximation)."""
    p = correct / total
    margin = z * math.sqrt(p * (1 - p) / total)
    return round(p - margin, 3), round(p + margin, 3)

print(accuracy_interval(52, 60))    # (0.781, 0.953)  -- 0.867 on 60 questions
print(accuracy_interval(520, 600))  # (0.839, 0.894)  -- same score, 10x the questions
```

With 60 eval questions, your "0.87" could plausibly be anywhere from about 0.78 to 0.95. That's why a change from 0.84 to 0.87 on a small eval set might be noise, and why growing your eval sets matters. Being able to say this in an interview marks you out.

## 4. Classic machine learning

Before deep learning there was (and still is, in most of industry) classic ML: linear and logistic regression, decision trees, random forests, gradient boosting, clustering, and the discipline around them: train/validation/test splits, overfitting, cross-validation, precision and recall.

Two good routes:

- **StatQuest** (Josh Starmer's YouTube channel): short, very clear videos on each algorithm and concept.
- **Andrew Ng's *Machine Learning Specialization*** (DeepLearning.AI): a structured course with exercises.

Practise with **scikit-learn**. Many real client problems ("predict which leads will convert", "flag unusual transactions") are better solved with a gradient-boosted model on tabular data than with an LLM, and knowing when *not* to use an LLM is a senior skill.

## 5. PyTorch and Hugging Face

Now the industrial tools:

- **PyTorch**: tensors, autograd, `nn.Module`, writing a training loop, data loaders, running on a GPU. After Karpathy this will feel familiar, because micrograd is a tiny PyTorch.
- **Hugging Face**: the Transformers library for loading open models, Datasets for data, and the free LLM course on their site.
- **Fine-tuning with LoRA** (via the PEFT library): training small adapter weights instead of the whole model, which makes fine-tuning possible on a single GPU. Learn when it's worth it: consistent formats, domain style, smaller and cheaper models that match a bigger model on a narrow task. Always compare against a well-prompted baseline with your evals.

Free GPU time on notebooks services such as Google Colab or Kaggle is enough for learning. Check current limits before planning a big run.

## 6. Stanford CS336: Language Modeling from Scratch

CS336 is a full Stanford course on building language models end to end: tokenisation, transformer architecture, training at scale, GPUs and kernels, parallelism, scaling laws, data, evaluation and alignment. The lectures are on Stanford Online's YouTube channel and the assignments are public. It's demanding, so treat it as a serious university course: one lecture plus its readings per week, and attempt the assignments.

You don't need to finish it to benefit. Even the first third will change how you read model release notes and papers.

## 7. Inference

The last step connects back to production: how models are actually served.

- **KV cache**: why generating each new token doesn't recompute attention over the whole prompt, and why long contexts use so much memory.
- **Batching and paged attention**: how servers like **vLLM** serve many requests at once efficiently.
- **Quantisation**: running models in 8-bit or 4-bit to cut memory and cost, and how to measure the quality loss.
- **Speculative decoding** and other latency tricks.
- **Prompt caching** from the provider side, which you've already used from the client side.

This knowledge pays off in both directions: you'll make better decisions about hosted APIs versus self-hosting open models for clients, and you'll be credible for roles on ML infrastructure teams.

## 8. Keep earning while you learn

The roadmap's plan is "the deep dive, once you're earning". Here's how to make both work:

- **Protect a fixed learning block.** For example, 6–8 hours a week: two weekday evenings and a weekend morning. Client work fills whatever time you give it; learning has to be scheduled first.
- **Keep retainers as your base.** Two or three small monthly retainers give steady income with predictable hours, which is ideal alongside study. Project work tops it up.
- **Raise prices instead of adding hours.** As your reviews and case studies grow, charge more per project rather than taking more projects.
- **Turn learning into content.** Every Karpathy video and CS336 lecture is a build-in-public post. Your audience grows with your depth.
- **Turn learning into services, slowly.** After PyTorch and LoRA, you can offer "evaluate whether fine-tuning a smaller model beats your current prompts". After inference, "cut your LLM bill" audits. Your new knowledge becomes new offers.
- **Keep the DSA habit light.** If you're aiming at big-tech internships, 2–3 NeetCode problems a day keeps you interview-ready without crowding out everything else.
- **Review quarterly.** Every three months: income, hours, what you learned, what you shipped. Adjust the split between earning and learning.

A simple weekly shape that works for many students who freelance:

| Block | Hours | What |
|---|---|---|
| University | as required | Classes and coursework come first |
| Client work | 10–15 | Retainers + one project at a time |
| Deep dive | 6–8 | Karpathy / maths / CS336 with code |
| Outreach and posting | 2–3 | 2 posts, follow-ups, a few pitches |
| DSA (if targeting big tech) | 2–4 | Short daily sessions |

## 9. An honest word

Here's the reality check from the roadmap: three months to **paid gigs or an AI internship** is realistic if you've shipped the projects and shown them publicly. A full-time AI engineer role usually needs some track record first, and gigs are how you build that track record.

Some things that are true and worth hearing now:

- **The first weeks of pitching often bring silence.** Few replies, some rejections, a proposal you were sure about going nowhere. That's normal, not a verdict on you. The numbers improve as you adjust your messages and your proof grows.
- **The first client is the hardest.** After one good review and one testimonial, everything gets easier.
- **Some months will be slow.** Retainers and a small savings buffer smooth that out.
- **You'll feel behind.** The field moves fast and someone will always seem further ahead. Compare yourself with where you were three months ago, when you were rusty at Python and had never called an LLM API. You've built and shipped four real systems since then.

You have a rare combination: engineering skills that are in demand, the ability to explain them, and the marketing sense to get them in front of people who'll pay. Keep shipping, keep measuring, keep showing your work, and keep learning what's inside the box. That compounds.

## Common mistakes

- **Stopping earning to "learn properly first".** Keep a base of income; learn alongside it.
- **Watching without coding.** Every video should end with code you wrote and ran.
- **Jumping straight to CS336 or fine-tuning.** Without the foundations, it's confusing and slow. Follow the order.
- **Fine-tuning because it sounds impressive.** Compare against a well-prompted baseline with evals; often prompting plus RAG wins.
- **Going quiet online while studying.** Your learning is your best content.
- **Burning out.** Students who freelance and study at once need rest in the plan, not just in theory.

## Recap

- The 2027 path, in order: Karpathy Zero to Hero, probability and statistics, classic ML, PyTorch and Hugging Face, Stanford CS336, inference.
- Code along with everything; measure and post what you learn.
- Probability makes your evals honest; classic ML tells you when not to use an LLM; inference knowledge makes you better at production.
- Keep earning with retainers and rising prices, a protected learning block, and learning turned into content and new services.
- Three months to paid work or an internship is realistic; full-time roles come with a track record. Keep going.
