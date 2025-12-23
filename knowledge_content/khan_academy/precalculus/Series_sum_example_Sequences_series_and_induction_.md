---
topic: precalculus.khan_academy
title: "Series sum example | Sequences, series and induction | Precalculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=A6fbDssPeac
video_id: A6fbDssPeac
difficulty: 2
content_type: video_summary
---

# Series sum example | Sequences, series and induction | Precalculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=A6fbDssPeac)*

## Key Concepts
- Infinite geometric series and their sums
- Simplifying factorial expressions
- Absolute value sums and telescoping patterns
- Algebraic manipulation to reveal cancellation patterns

## Definitions
- **Infinite geometric series**: A series of the form $a + ar + ar^2 + ar^3 + \cdots$ where $a$ is the first term and $r$ is the common ratio
- **Sum of infinite geometric series**: For $|r| < 1$, the sum converges to $S = \frac{a}{1-r}$
- **Factorial notation**: $n! = n \times (n-1) \times (n-2) \times \cdots \times 1$, with $0! = 1$

## Examples & Steps

### Step 1: Find a simplified expression for $s_k$
Given: $s_k$ is the sum of an infinite geometric series with:
- First term: $\frac{k-1}{k!}$
- Common ratio: $\frac{1}{k}$

Using the geometric series formula:
$$s_k = \frac{\frac{k-1}{k!}}{1 - \frac{1}{k}} = \frac{k-1}{k!} \cdot \frac{k}{k-1} = \frac{k}{k!}$$

Since $k! = k \cdot (k-1)!$, we simplify:
$$s_k = \frac{k}{k \cdot (k-1)!} = \frac{1}{(k-1)!}$$

Special cases:
- $s_1 = \frac{1}{0!} = 1$ (but original expression gives 0/1! = 0)
- $s_2 = \frac{1}{1!} = 1$

### Step 2: Analyze the main expression
We need to evaluate:
$$\frac{100^2}{100!} + \sum_{k=1}^{100} \left| (k^2 - 3k + 1) \cdot s_k \right|$$

Since $s_1 = 0$, the sum starts effectively from $k=2$:
- For $k=2$: $(4 - 6 + 1) \cdot 1 = (-1) \cdot 1 = -1$ → absolute value gives 1

So the expression becomes:
$$\frac{100^2}{100!} + 1 + \sum_{k=3}^{100} \left| (k^2 - 3k + 1) \cdot \frac{1}{(k-1)!} \right|$$

### Step 3: Simplify the algebraic expression
Rewrite $k^2 - 3k + 1$:
$$k^2 - 3k + 1 = (k-1)^2 - k$$

Thus the term becomes:
$$\frac{(k-1)^2 - k}{(k-1)!} = \frac{(k-1)^2}{(k-1)!} - \frac{k}{(k-1)!}$$

Simplify each part:
- $\frac{(k-1)^2}{(k-1)!} = \frac{k-1}{(k-2)!}$ (since $(k-1)! = (k-1)(k-2)!$)
- $\frac{k}{(k-1)!} = \frac{k}{(k-1)(k-2)!}$

### Step 4: Recognize telescoping pattern
The expression suggests a telescoping sum where intermediate terms cancel out, leaving only the first and last terms. The video shows that after algebraic manipulation, most terms cancel, simplifying the complex sum dramatically.

## Summary
This problem demonstrates how to simplify complex sums by first finding closed forms for series components, then using algebraic manipulation to reveal cancellation patterns. The key insight was rewriting $k^2-3k+1$ as $(k-1)^2-k$ to create terms that telescope when summed with factorial denominators.