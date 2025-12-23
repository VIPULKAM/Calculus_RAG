---
topic: precalculus.khan_academy
title: "Function inverses example 3 | Functions and their graphs | Algebra II | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=Bq9cq9FZuNM
video_id: Bq9cq9FZuNM
difficulty: 2
content_type: video_summary
---

# Function inverses example 3 | Functions and their graphs | Algebra II | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=Bq9cq9FZuNM)*

## Key Concepts
- Finding the inverse of a function with a restricted domain
- Handling the square root operation carefully when solving for the inverse
- Understanding how domain restrictions affect the choice of positive or negative square roots
- Graphing inverse functions as reflections over the line $y = x$

## Definitions
- **Inverse function**: A function that reverses the mapping of the original function. If $f(a) = b$, then $f^{-1}(b) = a$.
- **Restricted domain**: A subset of the original domain chosen to make the function one-to-one (necessary for inverses).
- **Principal square root**: The non-negative square root of a number (e.g., $\sqrt{9} = 3$).

## Examples & Steps
**Problem:** Find the inverse of $f(x) = (x - 1)^2 - 2$ with domain $x \leq 1$.

**Step 1 – Set up the equation**
\[
y = (x - 1)^2 - 2
\]
Domain: $x \leq 1$, Range: $y \geq -2$ (from graph observation).

**Step 2 – Solve for $x$ in terms of $y$**
Add 2 to both sides:
\[
y + 2 = (x - 1)^2
\]

**Step 3 – Take the square root carefully**
Since $x \leq 1$, $x - 1 \leq 0$ (negative). To recover the negative value, take the negative square root:
\[
-\sqrt{y + 2} = x - 1
\]

**Step 4 – Isolate $x$**
Add 1 to both sides:
\[
x = 1 - \sqrt{y + 2}
\]

**Step 5 – Write the inverse function**
\[
f^{-1}(y) = 1 - \sqrt{y + 2}, \quad \text{for } y \geq -2
\]
Renaming $y$ as $x$:
\[
f^{-1}(x) = 1 - \sqrt{x + 2}, \quad \text{for } x \geq -2
\]

**Step 6 – Graph the inverse**
Key points:
- $f^{-1}(-2) = 1$ → point $(-2, 1)$
- $f^{-1}(-1) = 0$ → point $(-1, 0)$
- $f^{-1}(2) = -1$ → point $(2, -1)$

The graph is a reflection of the original function across the line $y = x$.

## Summary
This lesson showed how to find the inverse of a quadratic function with a restricted domain. The key insight was recognizing that when $x \leq 1$, the expression $x - 1$ is negative, requiring the negative square root when solving. The inverse function's graph is a reflection of the original function across the line $y = x$.