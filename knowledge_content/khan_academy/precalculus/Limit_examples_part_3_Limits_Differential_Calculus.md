---
topic: precalculus.khan_academy
title: "Limit examples (part 3) | Limits | Differential Calculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=gWSDDopD9sk
video_id: gWSDDopD9sk
difficulty: 2
content_type: video_summary
---

# Limit examples (part 3) | Limits | Differential Calculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=gWSDDopD9sk)*

## Key Concepts
- Evaluating limits by direct substitution
- Handling indeterminate forms ($\frac{0}{0}$) through algebraic simplification
- Finding limits at infinity by comparing growth rates of terms
- Factoring polynomials to simplify rational expressions

## Definitions
- **Indeterminate form**: An expression like $\frac{0}{0}$ or $\frac{\infty}{\infty}$ that doesn't have a definite value without further analysis
- **Limit at infinity**: The value a function approaches as $x$ becomes arbitrarily large ($x \to \infty$)

## Examples & Steps

### Example 1: Limit with $\frac{0}{0}$ form
Find $\lim_{x \to 3} \frac{x^2 - 6x + 9}{x^2 - 9}$

**Step 1:** Try direct substitution
- Numerator: $3^2 - 6(3) + 9 = 9 - 18 + 9 = 0$
- Denominator: $3^2 - 9 = 9 - 9 = 0$
- Result: $\frac{0}{0}$ (indeterminate form)

**Step 2:** Factor both polynomials
- Numerator: $x^2 - 6x + 9 = (x - 3)^2$
- Denominator: $x^2 - 9 = (x + 3)(x - 3)$

**Step 3:** Simplify (for $x \ne 3$)
$$\frac{(x - 3)^2}{(x + 3)(x - 3)} = \frac{x - 3}{x + 3}$$

**Step 4:** Evaluate simplified limit
$$\lim_{x \to 3} \frac{x - 3}{x + 3} = \frac{3 - 3}{3 + 3} = \frac{0}{6} = 0$$

### Example 2: Another $\frac{0}{0}$ case
Find $\lim_{x \to 1} \frac{x^2 + x - 2}{x - 1}$

**Step 1:** Direct substitution gives $\frac{0}{0}$

**Step 2:** Factor numerator
$$x^2 + x - 2 = (x - 1)(x + 2)$$

**Step 3:** Simplify (for $x \ne 1$)
$$\frac{(x - 1)(x + 2)}{x - 1} = x + 2$$

**Step 4:** Evaluate simplified limit
$$\lim_{x \to 1} (x + 2) = 1 + 2 = 3$$

### Example 3: Limit at infinity
Find $\lim_{x \to \infty} \frac{x^2 + 3}{x^3}$

**Strategy:** Compare growth rates of terms
- Numerator's fastest-growing term: $x^2$
- Denominator's fastest-growing term: $x^3$
- Since $x^3$ grows faster than $x^2$, the fraction approaches 0

**Result:** $\lim_{x \to \infty} \frac{x^2 + 3}{x^3} = 0$

### Example 4: Limit at infinity with same degree
Find $\lim_{x \to \infty} \frac{3x^2 + x}{4x^2 - 5}$

**Strategy:** Compare leading coefficients
- Both numerator and denominator have $x^2$ as fastest-growing term
- Small terms ($x$ and $-5$) become negligible as $x \to \infty$
- Ratio of leading coefficients determines limit: $\frac{3}{4}$

**Result:** $\lim_{x \to \infty} \frac{3x^2 + x}{4x^2 - 5} = \frac{3}{4}$

## Summary
This lesson covered techniques for evaluating limits that initially give indeterminate forms like $\frac{0}{0}$. By factoring and simplifying rational expressions, we can often find the actual limit value. For limits at infinity, we compare the growth rates of terms - if degrees match, the limit is the ratio of leading coefficients; if denominators grow faster, the limit is 0.