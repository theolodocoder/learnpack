# Vectors, the dot product and cosine similarity

## Why this matters

When you build retrieval-augmented generation (RAG), every chunk of text you store becomes an **embedding**: a list of, say, 1,024 numbers. When a user asks a question, you embed the question too, and then find the chunks whose numbers "point the same way" as the question's. That comparison is the cosine similarity, and it is built from two operations: the dot product and the length of a vector. Understand those two and you understand the core of every vector database you will ever use.

## A vector is a list of numbers, and an arrow

A vector is an ordered list of numbers. `[3, 4]` is a vector with two **components**; an OpenAI or Voyage embedding is a vector with hundreds or thousands.

There are two ways to picture it, and you need both:

- **As a list:** the computer's view. Position `i` holds a number. That's all.
- **As an arrow:** the geometric view. `[3, 4]` is an arrow from the origin to the point 3 along x and 4 along y. In 1,024 dimensions you can't draw it, but everything you learn in 2-D (length, angle, "pointing the same way") still holds exactly.

In NumPy a vector is a 1-D array:

```python
import numpy as np

v = np.array([3.0, 4.0])
w = np.array([1.0, 2.0])

print(v.shape)   # (2,)
print(v + w)     # [4. 6.]   add component by component: arrows placed tip to tail
print(2 * v)     # [6. 8.]   scaling: same direction, twice as long
print(-v)        # [-3. -4.] same length, opposite direction
```

Adding vectors adds their components. Multiplying by a number (a **scalar**) stretches or shrinks the arrow. Those two operations are the whole of "linear" in linear algebra.

> **Note:** Always use NumPy arrays for maths, not Python lists. `[3, 4] + [1, 2]` is `[3, 4, 1, 2]` (list concatenation), and `2 * [3, 4]` is `[3, 4, 3, 4]`. Neither is what you meant.

## Length (the norm)

The length of a vector, written `‖v‖`, comes straight from Pythagoras. In 2-D, `[3, 4]` is the hypotenuse of a 3-by-4 right triangle, so its length is `√(3² + 4²) = 5`. In any number of dimensions:

```
‖v‖ = √(v₁² + v₂² + … + vₙ²)
```

```python
import math
import numpy as np

v = [3.0, 4.0]
print(math.sqrt(sum(x * x for x in v)))  # 5.0   by hand
print(np.linalg.norm(v))                 # 5.0   the NumPy way
```

A vector with length 1 is a **unit vector**. Dividing any non-zero vector by its length gives the unit vector pointing the same way. This is called **normalising**:

```python
import numpy as np

v = np.array([3.0, 4.0])
u = v / np.linalg.norm(v)
print(u)                   # [0.6 0.8]
print(np.linalg.norm(u))   # 1.0
```

A unit vector keeps only the *direction*. Hold on to that idea: for embeddings, direction is the meaning, and length mostly isn't.

## The dot product, algebraically

The dot product of two vectors of the same length multiplies them component by component and adds the results:

```
a · b = a₁b₁ + a₂b₂ + … + aₙbₙ
```

The result is a single number, not a vector.

```python
import numpy as np

a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, 5.0, 6.0])

print(sum(x * y for x, y in zip(a, b)))  # 32.0  (4 + 10 + 18), by hand
print(np.dot(a, b))                      # 32.0
print(a @ b)                             # 32.0  the @ operator: use this one
```

The `@` operator is Python's matrix-multiplication operator. For two 1-D arrays it is exactly the dot product. You'll see it everywhere in ML code.

Notice that a vector dotted with itself is the sum of its squares, so `‖v‖ = √(v · v)`.

## The dot product, geometrically

Here is the part that makes it useful. The same number also equals:

```
a · b = ‖a‖ · ‖b‖ · cos θ
```

where `θ` is the angle between the two arrows. So the dot product measures **how much two vectors point the same way**, scaled by their lengths:

| Angle between them | cos θ | Dot product |
|---|---|---|
| 0° (same direction) | 1 | large and positive |
| 90° (perpendicular) | 0 | exactly 0 |
| 180° (opposite) | −1 | large and negative |

Another way to see it: `a · b` is the length of `b`'s shadow (projection) onto `a`'s direction, times the length of `a`. If `b` sticks out at right angles to `a`, its shadow has length zero.

```python
import numpy as np

x_axis = np.array([1.0, 0.0])
print(x_axis @ np.array([5.0, 0.0]))   # 5.0   same direction
print(x_axis @ np.array([0.0, 7.0]))   # 0.0   perpendicular
print(x_axis @ np.array([-2.0, 0.0]))  # -2.0  opposite
print(x_axis @ np.array([3.0, 9.0]))   # 3.0   only the part along x counts
```

> **Try it:** pick two 2-D vectors, compute `a @ b`, then compute `np.linalg.norm(a) * np.linalg.norm(b) * np.cos(angle)` where `angle = np.arctan2(a[1], a[0]) - np.arctan2(b[1], b[0])`. They match.

## Cosine similarity

The dot product mixes two things: direction and length. A long vector gets a big dot product with everything. For comparing meaning, we want direction only, so we divide the lengths out:

```
cosine_similarity(a, b) = (a · b) / (‖a‖ · ‖b‖) = cos θ
```

The result is always between −1 and 1. 1 means "same direction", 0 means "unrelated", −1 means "opposite".

```python
import numpy as np

def cosine_similarity(a, b) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0   # a zero vector has no direction; we define its similarity as 0
    return float(a @ b / (na * nb))

print(cosine_similarity([1, 2], [2, 4]))     # 0.9999999999999998, i.e. 1.0 up to float rounding
print(cosine_similarity([1, 2], [100, 200])) # 1.0   length doesn't matter
print(cosine_similarity([1, 0], [0, 1]))     # 0.0
print(cosine_similarity([0, 0], [1, 1]))     # 0.0   our zero-vector rule
```

Floating-point arithmetic is rarely exact, so never test similarities with `==`. Use `math.isclose(x, 1.0)` or `np.isclose`.

Notice the zero-vector case. `[0, 0]` has length 0, so the formula divides by zero and NumPy gives `nan`. There's no "right" answer mathematically, so you have to choose one. Returning `0.0` ("no similarity") is the usual choice in search code: an empty document should never rank as a strong match.

Another useful fact: if both vectors are already unit length, cosine similarity is just the dot product. That's why vector databases often normalise every embedding once when it's stored. After that, every comparison is a single `@`.

## Embeddings plus cosine similarity *is* semantic search

An **embedding model** is a neural network trained so that texts with similar meaning end up as vectors pointing in similar directions. "How do I reset my password?" and "I forgot my login credentials" share almost no words, but their embeddings have a cosine similarity near 0.8 or 0.9. "Best pizza in Lagos" lands somewhere else entirely.

Given that, semantic search is three steps:

1. Embed every document once and store the vectors in a matrix, one row per document.
2. Embed the user's query.
3. Score every document by cosine similarity with the query and return the top `k`.

You can see the whole idea with hand-made 3-D "embeddings", where the dimensions loosely mean *account*, *food* and *travel*:

```python
import numpy as np

docs = ["Reset your password", "Update your billing email",
        "Best jollof rice recipes", "Cheap flights to Accra"]
doc_vecs = np.array([
    [0.9, 0.0, 0.1],
    [0.8, 0.1, 0.0],
    [0.0, 0.9, 0.2],
    [0.1, 0.2, 0.9],
])
query = np.array([0.8, 0.0, 0.1])     # "I can't log in"

scores = doc_vecs @ query / (np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query))
for i in np.argsort(-scores):
    print(f"{scores[i]:.3f}  {docs[i]}")
# 1.000  Reset your password
# 0.985  Update your billing email
# 0.227  Cheap flights to Accra
# 0.027  Best jollof rice recipes
```

A few NumPy details in that code:

- `doc_vecs @ query` dots every row with the query at once, giving one score per document. The next lesson explains why.
- `np.linalg.norm(doc_vecs, axis=1)` computes the length of each row. `axis=1` means "along the columns of each row".
- `np.argsort(-scores)` returns the indices that sort the scores from highest to lowest. Negating is the simple way to sort descending.

Real embeddings have 384 to 3,072 dimensions instead of 3, and no individual dimension means anything you can name. The maths is identical.

> **Note:** Some embedding providers return vectors already normalised to length 1. In that case the dot product and cosine similarity give the same ranking, and many vector databases let you pick "dot product" as the distance for speed. If you're not sure, normalise them yourself; it costs nothing.

## Common mistakes

- **Using Python lists for maths.** `+` and `*` on lists concatenate and repeat. Convert with `np.asarray` first.
- **Forgetting the zero vector.** Dividing by a zero norm gives `nan`, and `nan` silently poisons sorting: `np.argsort` puts `nan` last, but comparisons with `nan` are always `False`, so filters like `score > 0.5` quietly misbehave. Decide the rule (return `0.0`) and handle it explicitly.
- **Ranking by raw dot product with unnormalised vectors.** Long vectors win regardless of direction. Either normalise or use cosine similarity.
- **Mixing up `axis`.** For a matrix with one row per document, `axis=1` gives a value per row (per document); `axis=0` gives a value per column (per dimension).
- **Comparing embeddings from different models.** A vector from one model and a vector from another live in unrelated spaces. Their cosine similarity is meaningless, even if they have the same length.

## Recap

- A vector is a list of numbers and an arrow. NumPy 1-D arrays are vectors.
- Length: `‖v‖ = √(Σ vᵢ²)`, `np.linalg.norm(v)`. Dividing by it gives a unit vector (direction only).
- Dot product: `a · b = Σ aᵢbᵢ = ‖a‖‖b‖cos θ`, written `a @ b`. It measures how much two vectors point the same way, scaled by their lengths.
- Cosine similarity divides the lengths out: a number from −1 to 1 that depends only on direction. Define the zero-vector case as `0.0`.
- Semantic search is: embed everything, score by cosine similarity, take the top `k`. You'll write exactly that in the practice.
