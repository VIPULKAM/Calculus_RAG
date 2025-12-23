---
topic: precalculus.khan_academy
title: "Sequences and Series (part 1)"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=VgVJrSJxkDk
video_id: VgVJrSJxkDk
difficulty: 2
content_type: video_summary
---

# Sequences and Series (part 1)

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=VgVJrSJxkDk)*

Of course! Here are the study notes for the Khan Academy video "Sequences and Series (part 1)".

## Key Concepts
- Understanding what sequences and series are.
- Introduction to Sigma (Σ) notation for representing sums.
- Deriving the formula for the sum of an arithmetic series (sum of the first N positive integers).
- Introduction to the geometric series.

## Definitions
- **Sequence:** An ordered list of numbers. Example: 1, 2, 3, 4, ...
- **Series:** The sum of the terms of a sequence. Example: 1 + 2 + 3 + 4 + ...
- **Arithmetic Series:** The sum of an arithmetic sequence, where each term increases by a constant value. The specific example used is the sum of the first N integers: $1 + 2 + 3 + ... + N$.
- **Sigma (Σ) Notation:** A concise way to write the sum of a sequence.
    - Example: $\sum_{k=1}^{N} k$ means to sum the expression $k$ for all integer values of $k$ from 1 to $N$.
- **Geometric Series:** A series where each term is found by multiplying the previous term by a constant. The general form introduced is $a^0 + a^1 + a^2 + ... + a^N$, which is written as $\sum_{k=0}^{N} a^k$.

## Examples & Steps

### Deriving the Formula for an Arithmetic Series
**Goal:** Find a formula for the sum $S = 1 + 2 + 3 + ... + N$.

1.  Write the sum, $S$:
    $S = 1 + 2 + 3 + ... + (N-1) + N$

2.  Write the same sum in reverse order:
    $S = N + (N-1) + (N-2) + ... + 2 + 1$

3.  Add the two equations together, term by term:
    $S + S = (1 + N) + (2 + (N-1)) + (3 + (N-2)) + ... + ((N-1) + 2) + (N + 1)$
    This simplifies to:
    $2S = (N+1) + (N+1) + (N+1) + ... + (N+1)$

4.  Notice that there are $N$ terms of $(N+1)$.
    $2S = N \times (N+1)$

5.  Solve for $S$ by dividing both sides by 2:
    $S = \frac{N(N+1)}{2}$

**Result:** The sum of the first $N$ positive integers is $\sum_{k=1}^{N} k = \frac{N(N+1)}{2}$.

**Application Examples:**
-   Sum from 1 to 100: $\sum_{k=1}^{100} k = \frac{100 \times 101}{2} = \frac{10100}{2} = 5050$
-   Sum from 1 to 1000: $\sum_{k=1}^{1000} k = \frac{1000 \times 1001}{2} = \frac{1001000}{2} = 500500$

### Introducing the Geometric Series
**Goal:** Understand the form of a geometric series.
The series is defined as $S = \sum_{k=0}^{N} a^k$.
-   This expands to: $a^0 + a^1 + a^2 + a^3 + ... + a^N$, or $1 + a + a^2 + a^3 + ... + a^N$.
-   The video begins a method for finding the sum of this series by defining $S$ and then considering $aS$, but the derivation is continued in the next video.

## Summary
This video introduced the fundamental concepts of sequences and series, focusing on two main types. It explained how to use Sigma notation to write sums compactly and derived a powerful formula for the sum of an arithmetic series. It also introduced the geometric series, setting the stage for finding its sum in the next part.