---
topic: precalculus.khan_academy
title: "Combinations"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=bCxMhncR7PU
video_id: bCxMhncR7PU
difficulty: 2
content_type: video_summary
---

# Combinations

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=bCxMhncR7PU)*

## Key Concepts
- Permutations (arrangements where order matters)
- Combinations (selections where order doesn't matter)
- Relationship between permutations and combinations
- Factorial notation and calculations

## Definitions
- **Permutation**: The number of ways to arrange objects in order. For selecting $r$ items from $n$ items: $P(n,r) = \frac{n!}{(n-r)!}$
- **Combination**: The number of ways to select objects without regard to order. For selecting $r$ items from $n$ items: $C(n,r) = \binom{n}{r} = \frac{n!}{r!(n-r)!}$
- **Factorial**: $n! = n \times (n-1) \times (n-2) \times \cdots \times 1$

## Examples & Steps

### Permutation Example: 5 people in 3 chairs
**Step 1:** First chair: 5 choices  
**Step 2:** Second chair: 4 choices remaining  
**Step 3:** Third chair: 3 choices remaining  
**Calculation:** $5 \times 4 \times 3 = 60$ permutations  
**Formula:** $P(5,3) = \frac{5!}{(5-3)!} = \frac{5!}{2!} = 60$

### Combination Example: Groups of 3 from 5 people
**Step 1:** Calculate permutations: $P(5,3) = 60$  
**Step 2:** Divide by arrangements of 3 people: $3! = 6$  
**Calculation:** $\frac{60}{6} = 10$ combinations  
**Formula:** $C(5,3) = \binom{5}{3} = \frac{5!}{3!(5-3)!} = \frac{5!}{3! \cdot 2!} = 10$

## Summary
This lesson explains the difference between permutations (order matters) and combinations (order doesn't matter). The key insight is that combinations equal permutations divided by the number of ways to rearrange the selected items. The formulas $P(n,r) = \frac{n!}{(n-r)!}$ and $C(n,r) = \frac{n!}{r!(n-r)!}$ provide systematic ways to calculate these values.