---
topic: precalculus.khan_academy
title: "Compound interest and e (part 2) | Exponential and logarithmic functions | Algebra II | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=dzMvqJMLy9c
video_id: dzMvqJMLy9c
difficulty: 2
content_type: video_summary
---

# Compound interest and e (part 2) | Exponential and logarithmic functions | Algebra II | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=dzMvqJMLy9c)*

## Key Concepts
- Compound interest with increasing compounding frequency
- The limit definition of the mathematical constant $e$
- How compound interest approaches $e$ as compounding becomes continuous

## Definitions
- **Compound Interest Formula**:  
  If you borrow a principal $P$ at an interest rate $r$ compounded $n$ times per year, the amount owed after one year is:  
  $$
  A = P \left(1 + \frac{r}{n}\right)^n
  $$
- **The Number $e$**:  
  $e$ is defined as the limit:  
  $$
  e = \lim_{n \to \infty} \left(1 + \frac{1}{n}\right)^n
  $$
  $e$ is an irrational number approximately equal to $2.71828...$

## Examples & Steps
**Example 1: Daily Compounding**  
- Principal: $P = 1$ (for simplicity)  
- Annual interest rate: 100% ($r = 1$)  
- Compounding periods: $n = 365$ (daily)  
- Calculation:  
  $$
  A = \left(1 + \frac{1}{365}\right)^{365} \approx 2.7148
  $$

**Example 2: Hourly Compounding**  
- Hours in a year: $365 \times 24 = 8760$  
- Interest per hour: $\frac{1}{8760} \approx 0.000114$  
- Calculation:  
  $$
  A = \left(1 + \frac{1}{8760}\right)^{8760} \approx 2.71443
  $$

**Comparison of Compounding Frequencies**  
| Compounding Frequency | $n$ | Amount Owed ($A$) |
|-----------------------|-----|-------------------|
| Yearly                | 1   | $2.00$            |
| Monthly               | 12  | $\approx 2.613$   |
| Daily                 | 365 | $\approx 2.7148$  |
| Hourly                | 8760| $\approx 2.71443$ |

As $n$ increases, the amount approaches $e \approx 2.71828...$

## Summary
This lesson shows how compound interest calculations approach the mathematical constant $e$ as the compounding frequency increases. The limit definition $e = \lim_{n \to \infty} (1 + 1/n)^n$ demonstrates that continuous compounding results in a final amount of approximately $2.71828$, regardless of how small the compounding intervals become.