---
topic: precalculus.khan_academy
title: "Binomial theorem combinatorics connection | Algebra II | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=xF_hJaXUNfE
video_id: xF_hJaXUNfE
difficulty: 2
content_type: video_summary
---

# Binomial theorem combinatorics connection | Algebra II | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=xF_hJaXUNfE)*

## Key Concepts
- The connection between binomial expansion and combinatorics
- Why binomial coefficients appear in the binomial theorem
- How choosing terms from binomial factors relates to combinations

## Definitions
- **Binomial Theorem**: $(a + b)^n = \sum_{k=0}^{n} \binom{n}{k} a^{n-k} b^k$
- **Binomial Coefficient**: $\binom{n}{k}$ = number of ways to choose k items from n items
- **Combination**: A selection of items where order doesn't matter

## Examples & Steps

### Expanding $(a + b)^3$ using distribution:
1. Start with $(a + b)^3 = (a + b)(a + b)(a + b)$
2. First distribution: $a(a + b) + b(a + b)$
3. Expand: $a^2 + ab + ba + b^2$ (still multiplied by $(a + b)$)
4. Final expansion gives 8 terms:
   - $aaa$ → $a^3$
   - $aab, aba, baa$ → $3a^2b$
   - $abb, bab, bba$ → $3ab^2$
   - $bbb$ → $b^3$

### Combinatorics connection:
- Each term comes from choosing either $a$ or $b$ from each factor
- $a^3$: Choose $a$ from all 3 factors → $\binom{3}{3} = 1$ way
- $a^2b$: Choose $a$ from 2 factors, $b$ from 1 → $\binom{3}{2} = 3$ ways
- $ab^2$: Choose $a$ from 1 factor, $b$ from 2 → $\binom{3}{1} = 3$ ways
- $b^3$: Choose $b$ from all 3 factors → $\binom{3}{0} = 1$ way

## Summary
The binomial theorem uses combinations because when expanding $(a + b)^n$, each term's coefficient represents the number of ways to choose the $a$'s and $b$'s from the $n$ factors. The coefficient $\binom{n}{k}$ counts how many ways we can select $k$ instances of $b$ (or equivalently $n-k$ instances of $a$) from the $n$ factors, explaining why combinatorial numbers appear in binomial expansion.