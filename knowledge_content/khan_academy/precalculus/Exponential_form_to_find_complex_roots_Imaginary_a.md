---
topic: precalculus.khan_academy
title: "Exponential form to find complex roots | Imaginary and complex numbers | Precalculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=N0Y8ia57C24
video_id: N0Y8ia57C24
difficulty: 4
content_type: video_summary
---

# Exponential form to find complex roots | Imaginary and complex numbers | Precalculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=N0Y8ia57C24)*

## Key Concepts
- Exponential form of complex numbers and its utility
- Finding complex roots of equations like $x^n = 1$
- Visualizing complex roots on the Argand diagram
- Converting between exponential form and rectangular form ($a + bi$)

## Definitions
- **Complex number in exponential form**: $z = re^{i\theta}$, where:
  - $r$ is the magnitude (modulus) of $z$
  - $\theta$ is the argument (angle) of $z$
- **Argument of a complex number**: The angle $\theta$ the vector makes with the positive real axis. It is periodic: $\theta + 2\pi k$ (for integer $k$) represents the same direction.

## Examples & Steps

### Example: Finding the cube roots of 1
**Problem**: Solve $x^3 = 1$

**Step 1 – Express 1 in exponential form**
- $1 = 1 + 0i$
- Magnitude: $r = 1$
- Argument: $\theta = 0 + 2\pi k$ (for any integer $k$)
- So, $1 = e^{i(0 + 2\pi k)} = e^{i \cdot 2\pi k}$

**Step 2 – Rewrite the equation using different arguments**
- $x^3 = e^{i \cdot 0}$  
- $x^3 = e^{i \cdot 2\pi}$  
- $x^3 = e^{i \cdot 4\pi}$  
*(Using $k = 0, 1, 2$)*

**Step 3 – Take cube root of both sides**
- $x = (e^{i \cdot 2\pi k})^{1/3} = e^{i \cdot \frac{2\pi k}{3}}$
- For $k = 0$: $x_1 = e^{i \cdot 0} = 1$
- For $k = 1$: $x_2 = e^{i \cdot \frac{2\pi}{3}}$
- For $k = 2$: $x_3 = e^{i \cdot \frac{4\pi}{3}}$

**Step 4 – Visualize roots on Argand diagram**
- All roots have magnitude 1 (lie on unit circle)
- $x_1$: angle $0^\circ$ (positive real axis)
- $x_2$: angle $120^\circ$ ($\frac{2\pi}{3}$ radians)
- $x_3$: angle $240^\circ$ ($\frac{4\pi}{3}$ radians)
- Roots are equally spaced $120^\circ$ apart

**Step 5 – Convert to rectangular form ($a + bi$)**
- $x_2 = e^{i \cdot \frac{2\pi}{3}} = \cos\left(\frac{2\pi}{3}\right) + i\sin\left(\frac{2\pi}{3}\right) = -\frac{1}{2} + i\frac{\sqrt{3}}{2}$
- $x_3 = e^{i \cdot \frac{4\pi}{3}} = \cos\left(\frac{4\pi}{3}\right) + i\sin\left(\frac{4\pi}{3}\right) = -\frac{1}{2} - i\frac{\sqrt{3}}{2}$

## Summary
The exponential form of complex numbers is particularly useful for finding roots of equations like $x^n = 1$. By expressing 1 as $e^{i \cdot 2\pi k}$ and taking the nth root, we obtain n distinct complex roots equally spaced around the unit circle. This method can be extended to find any nth roots of complex numbers.