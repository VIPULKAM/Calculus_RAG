---
topic: precalculus.khan_academy
title: "Introduction to limits | Limits | Differential Calculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=riXcZT2ICjA
video_id: riXcZT2ICjA
difficulty: 1
content_type: video_summary
---

# Introduction to limits | Limits | Differential Calculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=riXcZT2ICjA)*

## Key Concepts
- The concept of a limit: what value a function approaches as the input approaches a specific point.
- Functions can be undefined at a point but still have a limit as they approach that point.
- The limit describes the function's behavior *near* a point, not necessarily *at* the point.

## Definitions
- **Limit**: The value that a function $f(x)$ approaches as the variable $x$ approaches a specific value. Notation: $\lim_{x \to a} f(x) = L$.
- **Undefined Point**: A value $x = a$ where the function has no defined output, often due to division by zero or a point discontinuity.

## Examples & Steps

### Example 1: Simplifying a Rational Function
**Function:** $f(x) = \frac{x-1}{x-1}$

**Step 1: Simplification**
- For all $x \neq 1$, the numerator and denominator are equal, so the expression simplifies to $f(x) = 1$.
- However, at $x = 1$, the function is undefined because it results in $\frac{0}{0}$.

**Step 2: Graphing the Function**
- The graph is a horizontal line at $y=1$, but with a hole (open circle) at the point $(1, 1)$ to indicate it is undefined there.

**Step 3: Finding the Limit**
- As $x$ gets closer to 1 from either side, $f(x)$ gets closer to 1.
- Therefore, $\lim_{x \to 1} f(x) = 1$, even though $f(1)$ is undefined.

### Example 2: A Function with a Discontinuity
**Function:**
\[
g(x) =
\begin{cases}
x^2 & \text{if } x \neq 2 \\
1 & \text{if } x = 2
\end{cases}
\]

**Step 1: Evaluating the Function at $x=2$**
- By definition, $g(2) = 1$.

**Step 2: Finding the Limit as $x$ approaches 2**
- As $x$ gets closer to 2 (e.g., 1.9, 1.999, 2.1, 2.001), the value of $g(x)$ gets closer to $2^2 = 4$.
- The limit is determined by the behavior of the function *near* $x=2$, not the value *at* $x=2$.
- Therefore, $\lim_{x \to 2} g(x) = 4$, even though $g(2) = 1$.

## Summary
This video introduces the fundamental concept of a limit in calculus. A limit describes the value a function approaches as its input gets arbitrarily close to a certain point, which may be different from the function's actual value at that point. Through examples, we see that limits help analyze function behavior near points of discontinuity, forming the basis for further calculus concepts.