---
topic: precalculus.khan_academy
title: "Complex determinant example | Imaginary and complex numbers | Precalculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=E7OkUomRq1Q
video_id: E7OkUomRq1Q
difficulty: 4
content_type: video_summary
---

# Complex determinant example | Imaginary and complex numbers | Precalculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=E7OkUomRq1Q)*

Of course! Here are the study notes based on the Khan Academy video transcript.

## Key Concepts
- Evaluating a 3x3 determinant with complex number entries.
- Using Euler's formula to simplify powers of complex numbers.
- Solving a cubic equation in the complex variable z by recognizing that the determinant simplifies to a known factorization.

## Definitions
- **Complex Number:** A number of the form $a + bi$, where $a$ and $b$ are real numbers and $i$ is the imaginary unit ($i^2 = -1$).
- **Euler's Formula:** $e^{i\theta} = \cos \theta + i \sin \theta$.
- **Root of Unity:** A complex number that yields 1 when raised to a positive integer power. In this problem, $\omega$ is a cube root of unity, meaning $\omega^3 = 1$.

## Examples & Steps
**Problem:** Let $\omega = \cos\left(\frac{2\pi}{3}\right) + i \sin\left(\frac{2\pi}{3}\right)$. Find the number of distinct complex numbers $z$ that satisfy the following equation (where the determinant is set to zero):

$$
\begin{vmatrix}
z + 1 & \omega & \omega^2 \\
\omega & z + \omega^2 & 1 \\
\omega^2 & 1 & z + \omega
\end{vmatrix} = 0
$$

**Step 1: Evaluate the Determinant**
Using the cofactor expansion along the first row, the determinant is:
$$(z+1)\begin{vmatrix} z+\omega^2 & 1 \\ 1 & z+\omega \end{vmatrix} - \omega \begin{vmatrix} \omega & 1 \\ \omega^2 & z+\omega \end{vmatrix} + \omega^2 \begin{vmatrix} \omega & z+\omega^2 \\ \omega^2 & 1 \end{vmatrix} = 0$$

**Step 2: Expand the 2x2 Determinants**
Calculate each 2x2 determinant:
1. $\begin{vmatrix} z+\omega^2 & 1 \\ 1 & z+\omega \end{vmatrix} = (z+\omega^2)(z+\omega) - (1)(1) = z^2 + (\omega + \omega^2)z + \omega^3 - 1$
2. $\begin{vmatrix} \omega & 1 \\ \omega^2 & z+\omega \end{vmatrix} = (\omega)(z+\omega) - (1)(\omega^2) = \omega z + \omega^2 - \omega^2 = \omega z$
3. $\begin{vmatrix} \omega & z+\omega^2 \\ \omega^2 & 1 \end{vmatrix} = (\omega)(1) - (\omega^2)(z+\omega^2) = \omega - \omega^2 z - \omega^4$

Substitute these back into the main equation:
$$(z+1)[z^2 + (\omega + \omega^2)z + \omega^3 - 1] - \omega[\omega z] + \omega^2[\omega - \omega^2 z - \omega^4] = 0$$

**Step 3: Simplify Using Properties of $\omega$**
The complex number $\omega = e^{2\pi i/3}$ is a primitive cube root of unity. Its key properties are:
- $\omega^3 = 1$
- $1 + \omega + \omega^2 = 0$ (which also implies $\omega + \omega^2 = -1$)
- Higher powers cycle: $\omega^4 = \omega$, $\omega^6 = (\omega^3)^2 = 1$

Substitute these identities into the expanded equation:
- $\omega^3 - 1 = 1 - 1 = 0$
- $\omega + \omega^2 = -1$
- The entire equation simplifies dramatically to:
$$(z+1)(z^2 - z) = z(z+1)(z-1) = 0$$

**Step 4: Solve the Simplified Equation**
The equation $z(z+1)(z-1) = 0$ has three solutions:
$$z = 0, \quad z = 1, \quad z = -1$$
These are three distinct complex numbers.

## Summary
The video demonstrates how to solve a complex determinant equation by expanding the determinant and then simplifying the result using the algebraic properties of a cube root of unity ($\omega$). The key insight is that the complicated-looking determinant simplifies to a simple cubic equation, $z^3 - z = 0$, revealing that there are exactly three distinct solutions for $z$.