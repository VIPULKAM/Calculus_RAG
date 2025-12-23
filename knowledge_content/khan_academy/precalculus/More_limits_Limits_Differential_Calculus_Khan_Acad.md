---
topic: precalculus.khan_academy
title: "More limits | Limits | Differential Calculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=rkeU8_4nzKo
video_id: rkeU8_4nzKo
difficulty: 2
content_type: video_summary
---

# More limits | Limits | Differential Calculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=rkeU8_4nzKo)*

## Key Concepts
- Evaluating limits involving absolute values by considering left-hand and right-hand limits
- Using substitution to transform limit problems into known forms
- Applying the standard limit result $\lim_{x \to 0} \frac{\sin x}{x} = 1$

## Definitions
- **Absolute Value**: $|x| = \begin{cases} x & \text{if } x \geq 0 \\ -x & \text{if } x < 0 \end{cases}$
- **Limit Existence**: $\lim_{x \to a} f(x)$ exists if and only if $\lim_{x \to a^-} f(x) = \lim_{x \to a^+} f(x)$

## Examples & Steps

### Example 1: Limit with Absolute Value
Find $\lim_{x \to 0} \frac{x - 2|x|}{|x|}$

**Step 1 – Right-hand limit** ($x \to 0^+$)
- For $x > 0$, $|x| = x$
- $\lim_{x \to 0^+} \frac{x - 2x}{x} = \lim_{x \to 0^+} \frac{-x}{x} = -1$

**Step 2 – Left-hand limit** ($x \to 0^-$)
- For $x < 0$, $|x| = -x$
- $\lim_{x \to 0^-} \frac{x - 2(-x)}{-x} = \lim_{x \to 0^-} \frac{x + 2x}{-x} = \lim_{x \to 0^-} \frac{3x}{-x} = -3$

**Step 3 – Conclusion**
- Since $-1 \neq -3$, the limit does not exist

### Example 2: Trigonometric Limit
Find $\lim_{x \to 0} \frac{\sin(5x)}{2x}$

**Step 1 – Substitution**
- Let $a = 5x$, so $x = \frac{a}{5}$
- As $x \to 0$, $a \to 0$

**Step 2 – Rewrite limit**
- $\lim_{x \to 0} \frac{\sin(5x)}{2x} = \lim_{a \to 0} \frac{\sin a}{2 \cdot (a/5)} = \lim_{a \to 0} \frac{\sin a}{(2a/5)}$

**Step 3 – Simplify**
- $= \lim_{a \to 0} \frac{5}{2} \cdot \frac{\sin a}{a} = \frac{5}{2} \cdot \lim_{a \to 0} \frac{\sin a}{a}$

**Step 4 – Apply known limit**
- Since $\lim_{a \to 0} \frac{\sin a}{a} = 1$, the result is $\frac{5}{2}$

## Summary
This lesson showed how to handle limits with absolute values by analyzing left and right approaches separately. It also demonstrated using substitution to transform trigonometric limits into the standard form $\frac{\sin x}{x}$, whose limit is known to be 1. These techniques expand our ability to evaluate more complex limit problems.