---
topic: precalculus.khan_academy
title: "Binomial Theorem (part 1)"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=Cv4YhIMfbeM
video_id: Cv4YhIMfbeM
difficulty: 2
content_type: video_summary
---

# Binomial Theorem (part 1)

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=Cv4YhIMfbeM)*

## Key Concepts
- Binomial Theorem: A formula for expanding expressions of the form $(a + b)^n$ without manual multiplication
- Binomial Coefficients: The numbers $\binom{n}{k}$ that appear as coefficients in the expansion
- Pattern Recognition: How exponents of $a$ and $b$ change systematically in each term

## Definitions
- **Binomial**: A polynomial with two terms (e.g., $a + b$)
- **Binomial Coefficient**: The number of ways to choose $k$ items from $n$ items, denoted $\binom{n}{k} = \frac{n!}{k!(n-k)!}$
- **Binomial Theorem**: For any positive integer $n$:
  $$(a + b)^n = \sum_{k=0}^n \binom{n}{k} a^{n-k} b^k$$

## Examples & Steps
**Example: Expand $(a + b)^4$ using the binomial theorem**

**Step 1 – Apply the formula:**
$$(a + b)^4 = \sum_{k=0}^4 \binom{4}{k} a^{4-k} b^k$$

**Step 2 – Write all terms:**
$$= \binom{4}{0}a^4b^0 + \binom{4}{1}a^3b^1 + \binom{4}{2}a^2b^2 + \binom{4}{3}a^1b^3 + \binom{4}{4}a^0b^4$$

**Step 3 – Calculate binomial coefficients:**
- $\binom{4}{0} = \frac{4!}{0!4!} = 1$
- $\binom{4}{1} = \frac{4!}{1!3!} = 4$
- $\binom{4}{2} = \frac{4!}{2!2!} = 6$
- $\binom{4}{3} = \frac{4!}{3!1!} = 4$
- $\binom{4}{4} = \frac{4!}{4!0!} = 1$

**Step 4 – Substitute coefficients:**
$$(a + b)^4 = 1a^4 + 4a^3b + 6a^2b^2 + 4ab^3 + 1b^4$$

**Final Answer:**
$$(a + b)^4 = a^4 + 4a^3b + 6a^2b^2 + 4ab^3 + b^4$$

## Summary
The binomial theorem provides a systematic way to expand binomials raised to any power using binomial coefficients. The exponents of $a$ decrease from $n$ to $0$ while the exponents of $b$ increase from $0$ to $n$ across the terms. This method is much more efficient than repeatedly multiplying the binomial manually.