---
topic: precalculus.khan_academy
title: "Benford's law explanation (sequel to mysteries of Benford's law) | Algebra II | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=SZUDoEdjTzg
video_id: SZUDoEdjTzg
difficulty: 2
content_type: video_summary
---

# Benford's law explanation (sequel to mysteries of Benford's law) | Algebra II | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=SZUDoEdjTzg)*

## Key Concepts
- Benford's Law: The phenomenon where the leading digits of many real-world datasets are not uniformly distributed, but follow a specific logarithmic pattern.
- Logarithmic Scale: A scale where equal distances represent multiplicative factors (e.g., powers of 10), not additive changes.
- Exponential Growth: Processes that grow by a fixed percentage over time (e.g., populations, financial data), which tend to follow Benford’s Law.

## Definitions
- **Benford’s Law**: A probability distribution for the first digit \(d\) (where \(d \in \{1,2,\dots,9\}\)) of a number, given by:  
  \[
  P(d) = \log_{10}\left(1 + \frac{1}{d}\right)
  \]
  For example, \(P(1) \approx 30.1\%\), \(P(2) \approx 17.6\%\), etc.
- **Logarithmic Scale**: A scale where values are spaced by their logarithm. On a base-10 log scale, the distance from 1 to 10 is the same as from 10 to 100.
- **Most Significant Digit**: The first non-zero digit of a number (e.g., the 1 in 123 or 0.0123).

## Examples & Steps
### Example: Powers of 2 on a Logarithmic Scale
1. List the first few powers of 2:  
   \(2^0 = 1\), \(2^1 = 2\), \(2^2 = 4\), \(2^3 = 8\), \(2^4 = 16\), \(2^5 = 32\), \(2^6 = 64\), ...
2. Plot these values on a base-10 logarithmic scale:
   - 1 is at the start of the scale.
   - 2 is in the interval [1, 10).
   - 4, 8, 16, 32, 64 all fall within intervals [1, 10), [10, 100), etc.
3. Observe that the powers of 2 are equally spaced on the log scale because each step multiplies by 2.
4. The probability of a value falling in an interval \([d, d+1)\) (or \([10d, 10(d+1))\), etc.) is proportional to the length of that interval on the log scale.  
   - The length of \([1, 2)\) on a log scale is \(\log_{10}(2) - \log_{10}(1) = \log_{10}(2)\).
   - The length of \([2, 3)\) is \(\log_{10}(3) - \log_{10}(2)\).
   - Thus, the probability of a digit \(d\) is:  
     \[
     P(d) = \frac{\log_{10}(d+1) - \log_{10}(d)}{\log_{10}(10) - \log_{10}(1)} = \log_{10}\left(1 + \frac{1}{d}\right)
     \]
   This matches Benford’s Law.

## Summary
Benford’s Law arises when numbers are distributed across multiple orders of magnitude, such as in exponentially growing sequences like powers of 2 or population data. On a logarithmic scale, the intervals for numbers starting with 1 (e.g., 1–2, 10–20) are larger, making them more likely to contain values. This explains why many real-world datasets follow Benford’s Law, especially those involving exponential growth or decline.