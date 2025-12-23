---
topic: precalculus.khan_academy
title: "Permutations"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=XqQTXW7XfYA
video_id: XqQTXW7XfYA
difficulty: 2
content_type: video_summary
---

# Permutations

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=XqQTXW7XfYA)*

## Key Concepts
- Permutations: Arrangements of objects where order matters
- Counting principle for arranging items in ordered positions
- Formula derivation for permutations
- Difference between permutations and combinations (order vs. selection only)

## Definitions
- **Permutation**: An ordered arrangement of objects where the sequence matters
- **Permutation Notation**: $nPk$ = number of ways to arrange $n$ items in $k$ ordered positions
- **Permutation Formula**: $nPk = \frac{n!}{(n-k)!}$

## Examples & Steps

### Example 1: 7 People in 3 Chairs
**Problem**: How many ways can 7 people sit in 3 chairs?
- Chair 1: 7 choices (all people standing)
- Chair 2: 6 choices (1 person already seated)
- Chair 3: 5 choices (2 people already seated)

**Solution**: $7 × 6 × 5 = 210$ arrangements

**Using formula**: $7P3 = \frac{7!}{(7-3)!} = \frac{7!}{4!} = \frac{7×6×5×4×3×2×1}{4×3×2×1} = 7×6×5 = 210$

### Example 2: 3 Balls in 2 Cups
**Problem**: How many ways to place 3 distinct balls (A, B, C) in 2 cups?
- Cup 2: 3 choices (all balls available)
- Cup 1: 2 choices (1 ball already placed)

**Solution**: $3 × 2 = 6$ arrangements

**All arrangements**:
- A in cup 1, B in cup 2
- B in cup 1, A in cup 2  
- A in cup 1, C in cup 2
- C in cup 1, A in cup 2
- B in cup 1, C in cup 2
- C in cup 1, B in cup 2

**Using formula**: $3P2 = \frac{3!}{(3-2)!} = \frac{3!}{1!} = \frac{6}{1} = 6$

## Summary
Permutations count ordered arrangements where sequence matters. The formula $nPk = \frac{n!}{(n-k)!}$ calculates how many ways to arrange $n$ items in $k$ positions by taking the first $k$ factors of $n!$. This differs from combinations where order doesn't matter.