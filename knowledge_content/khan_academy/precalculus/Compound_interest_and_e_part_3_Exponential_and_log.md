---
topic: precalculus.khan_academy
title: "Compound interest and e (part 3) | Exponential and logarithmic functions | Algebra II | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=sQYpUJV8foY
video_id: sQYpUJV8foY
difficulty: 2
content_type: video_summary
---

# Compound interest and e (part 3) | Exponential and logarithmic functions | Algebra II | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=sQYpUJV8foY)*

## Key Concepts
- Continuous compound interest
- The mathematical constant $e$
- Limits and their application to exponential growth
- Generalizing compound interest formulas for any interest rate

## Definitions
- **Compound Interest Formula**: $A = P \left(1 + \frac{r}{n}\right)^{nt}$  
  Where:  
  $A$ = final amount  
  $P$ = principal (initial amount)  
  $r$ = annual interest rate (as a decimal)  
  $n$ = number of compounding periods per year  
  $t$ = time in years

- **Continuous Compounding**: The limit as compounding frequency approaches infinity  
  $\lim_{n \to \infty} P \left(1 + \frac{r}{n}\right)^{nt} = Pe^{rt}$

- **Mathematical Constant $e$**:  
  $e = \lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x \approx 2.71828...$

## Examples & Steps
**Example: Deriving Continuous Compounding Formula**

1. **Start with general compound interest formula**:  
   $A = P \left(1 + \frac{r}{n}\right)^n$ (for $t = 1$ year)

2. **Take limit as $n \to \infty$**:  
   $\lim_{n \to \infty} P \left(1 + \frac{r}{n}\right)^n$

3. **Make substitution**: Let $\frac{1}{x} = \frac{r}{n}$  
   - This implies $n = xr$
   - As $n \to \infty$, $x \to \infty$

4. **Rewrite the limit**:  
   $\lim_{x \to \infty} P \left(1 + \frac{1}{x}\right)^{xr}$

5. **Apply exponent rules**:  
   $\lim_{x \to \infty} P \left[\left(1 + \frac{1}{x}\right)^x\right]^r$

6. **Recognize the definition of $e$**:  
   $P \cdot e^r$

**Numerical Example**:  
If $P = \$50$, $r = 10\% = 0.10$, compounded continuously for 1 year:  
$A = 50 \cdot e^{0.10} \approx 50 \cdot 1.10517 = \$55.26$

## Summary
This lesson showed how compound interest formulas approach the continuous compounding formula $Pe^{rt}$ as the number of compounding periods increases infinitely. The mathematical constant $e$ emerges naturally from this limiting process, demonstrating its fundamental role in modeling exponential growth. The derivation involved limit calculations and variable substitution to connect compound interest to the definition of $e$.