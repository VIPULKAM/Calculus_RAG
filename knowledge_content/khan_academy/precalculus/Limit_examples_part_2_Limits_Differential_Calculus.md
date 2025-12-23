---
topic: precalculus.khan_academy
title: "Limit examples (part 2) | Limits | Differential Calculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=YRw8udexH4o
video_id: YRw8udexH4o
difficulty: 2
content_type: video_summary
---

# Limit examples (part 2) | Limits | Differential Calculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=YRw8udexH4o)*

Of course! Here are the study notes for the Khan Academy video transcript.

## Key Concepts
- Understanding one-sided limits (from the positive and negative sides)
- Determining when a limit is undefined vs. when it equals infinity
- How the behavior of a function (like $1/x$ vs. $1/x^2$) affects its limit as it approaches a point

## Definitions
- **One-Sided Limit**: The value a function approaches as the input approaches a specific point *from one side only*.
    - **Limit from the right (positive side)**: $\lim_{x \to a^+} f(x)$
    - **Limit from the left (negative side)**: $\lim_{x \to a^-} f(x)$
- **Limit is Undefined**: A limit does not exist if the one-sided limits are not equal. For example, if the function approaches positive infinity from one side and negative infinity from the other.
- **Limit Equals Infinity**: If a function increases without bound (goes to $\infty$) or decreases without bound (goes to $-\infty$) as it approaches a point, and this behavior is the same from both sides, we say the limit is $\infty$ or $-\infty$.

## Examples & Steps

### Example 1: Limit of $1/x$ as $x$ approaches 0
**Step 1: Analyze from the positive side ($x \to 0^+$)**
- Evaluate the function with positive numbers getting closer to 0.
- When $x = 0.1$, $f(0.1) = 1/0.1 = 10$
- When $x = 0.001$, $f(0.001) = 1/0.001 = 1,000$
- As $x$ gets closer to 0 from the right, $f(x)$ becomes a larger and larger positive number.
- **Conclusion:** $\lim_{x \to 0^+} \frac{1}{x} = \infty$

**Step 2: Analyze from the negative side ($x \to 0^-$)**
- Evaluate the function with negative numbers getting closer to 0.
- When $x = -0.1$, $f(-0.1) = 1/(-0.1) = -10$
- When $x = -0.001$, $f(-0.001) = 1/(-0.001) = -1,000$
- As $x$ gets closer to 0 from the left, $f(x)$ becomes a larger and larger negative number (or a smaller and smaller number).
- **Conclusion:** $\lim_{x \to 0^-} \frac{1}{x} = -\infty$

**Step 3: Compare the one-sided limits**
- The limit from the right is $\infty$.
- The limit from the left is $-\infty$.
- Since they are not equal, the overall limit is undefined.
- **Final Answer:** $\lim_{x \to 0} \frac{1}{x}$ is **undefined**.

### Example 2: Limit of $1/x^2$ as $x$ approaches 0
**Step 1: Analyze from both sides**
- Because $x$ is squared, the result is always positive, whether $x$ is positive or negative.
- When $x = 0.1$, $f(0.1) = 1/(0.1)^2 = 1/0.01 = 100$
- When $x = -0.1$, $f(-0.1) = 1/(-0.1)^2 = 1/0.01 = 100$
- As $x$ approaches 0 from *either* side, $f(x)$ becomes a larger and larger positive number.
- **Conclusion:** $\lim_{x \to 0^+} \frac{1}{x^2} = \infty$ and $\lim_{x \to 0^-} \frac{1}{x^2} = \infty$

**Step 2: Compare the one-sided limits**
- The limit from the right is $\infty$.
- The limit from the left is $\infty$.
- Since they are equal, the overall limit is $\infty$.
- **Final Answer:** $\lim_{x \to 0} \frac{1}{x^2} = \infty$

## Summary
This lesson taught how to evaluate limits by checking the behavior of a function from the left and right sides of a point. A limit is only defined if both one-sided limits are equal. The function $1/x$ has an undefined limit at 0 because its sides approach $+\infty$ and $-\infty$, while $1/x^2$ has a limit of $\infty$ at 0 because both sides approach positive infinity.