---
topic: precalculus.khan_academy
title: "2003 AIME II problem 8 | AIME | Math for fun and glory | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=ZFN63oTeYzc
video_id: ZFN63oTeYzc
difficulty: 2
content_type: video_summary
---

# 2003 AIME II problem 8 | AIME | Math for fun and glory | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=ZFN63oTeYzc)*

## Key Concepts
- Arithmetic sequences: sequences where each term increases by a constant difference
- Product sequences: sequences formed by multiplying corresponding terms of two other sequences
- Solving systems of equations to find unknown variables in sequences

## Definitions
- **Arithmetic sequence**: A sequence where the difference between consecutive terms is constant.  
  General form: $a, a+d, a+2d, a+3d, \dots$
- **Product sequence**: If $\{a_n\}$ and $\{b_n\}$ are two sequences, their product sequence is $\{c_n\}$ where $c_n = a_n \cdot b_n$

## Examples & Steps
**Problem**: Find the 8th term of the sequence 1440, 1716, 1848, ... formed by multiplying corresponding terms of two arithmetic sequences.

**Step 1 – Define the sequences**  
Let the first arithmetic sequence be: $A, A+M, A+2M, \dots, A+7M$  
Let the second arithmetic sequence be: $B, B+N, B+2N, \dots, B+7N$

**Step 2 – Set up equations from given terms**  
- 1st term: $A \cdot B = 1440$  
- 2nd term: $(A+M)(B+N) = 1716$  
- 3rd term: $(A+2M)(B+2N) = 1848$

**Step 3 – Expand and simplify equations**  
From 2nd term: $(A+M)(B+N) = AB + AN + BM + MN = 1716$  
Subtract 1st term: $AN + BM + MN = 1716 - 1440 = 276$  **(1)**

From 3rd term: $(A+2M)(B+2N) = AB + 2AN + 2BM + 4MN = 1848$  
Subtract 1st term: $2AN + 2BM + 4MN = 1848 - 1440 = 408$  
Divide by 2: $AN + BM + 2MN = 204$  **(2)**

**Step 4 – Solve for variables**  
Subtract equation (1) from equation (2):  
$(AN + BM + 2MN) - (AN + BM + MN) = 204 - 276$  
$MN = -72$

Substitute into equation (1):  
$AN + BM + (-72) = 276$  
$AN + BM = 348$

**Step 5 – Find the 8th term**  
8th term = $(A+7M)(B+7N) = AB + 7AN + 7BM + 49MN$  
$= 1440 + 7(348) + 49(-72)$  
$= 1440 + 2436 - 3528$  
$= 1440 + 2436 = 3876$, then $3876 - 3528 = 348$

**Final answer**: The 8th term is $\boxed{348}$

## Summary
This problem demonstrated how to work with sequences formed by multiplying two arithmetic sequences. By expanding the product terms and solving the resulting system of equations, we found the values needed to calculate any term in the product sequence. The key insight was recognizing the pattern in the expanded binomial products.