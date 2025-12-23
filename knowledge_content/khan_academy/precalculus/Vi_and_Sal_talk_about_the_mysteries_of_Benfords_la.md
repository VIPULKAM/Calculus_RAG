---
topic: precalculus.khan_academy
title: "Vi and Sal talk about the mysteries of Benford's law | Logarithms | Algebra II | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=6KmeGpjeLZ0
video_id: 6KmeGpjeLZ0
difficulty: 2
content_type: video_summary
---

# Vi and Sal talk about the mysteries of Benford's law | Logarithms | Algebra II | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=6KmeGpjeLZ0)*

## Key Concepts
- Benford's Law: A mathematical phenomenon where the first digit of numbers in many real-world datasets is not uniformly distributed.
- Probability distribution of first digits: The likelihood that a number's first digit is 1, 2, ..., 9 follows a specific logarithmic pattern.
- Applications: The law appears in diverse datasets like country populations, financial data, physical constants, and mathematical sequences.

## Definitions
- **Benford's Law**: The probability that the first digit of a number is $d$ (where $d = 1, 2, ..., 9$) is given by:
  $$
  P(d) = \log_{10}\left(1 + \frac{1}{d}\right)
  $$
- **First Digit**: The leftmost non-zero digit of a number (e.g., the first digit of 1,300,000,000 is 1).

## Examples & Steps
**Example 1: Country Populations**
- Step 1: List all countries and their populations.
- Step 2: For each population, identify the first digit (e.g., Vatican City: ~1,000 → first digit = 1).
- Step 3: Count how many populations start with 1, 2, ..., 9.
- Step 4: Compare the distribution to Benford’s Law. In the video, ~27 countries had populations starting with 1, which is a higher proportion than those starting with 8 or 9.

**Example 2: Powers of 2**
- Step 1: Generate the sequence: $2^0 = 1$, $2^1 = 2$, $2^2 = 4$, $2^3 = 8$, $2^4 = 16$, $2^5 = 32$, $2^6 = 64$, $2^7 = 128$, $2^8 = 256$, $2^9 = 512$, ...
- Step 2: Extract first digits: 1, 2, 4, 8, 1, 3, 6, 1, 2, 5, ...
- Step 3: As the sequence grows, the proportion of numbers starting with each digit converges to the probabilities predicted by Benford’s Law.

## Summary
Benford's Law describes the surprising pattern where the digit 1 appears as the first digit in real-world numbers about 30% of the time, while higher digits like 9 appear less than 5% of the time. This distribution arises naturally in many datasets, including populations, financial figures, and even mathematical sequences like the powers of 2. The law is mathematically expressed as a logarithmic probability function.