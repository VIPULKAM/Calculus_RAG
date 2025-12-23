---
topic: precalculus.khan_academy
title: "Basic complex analysis | Imaginary and complex numbers | Precalculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=FwuPXchH2rA
video_id: FwuPXchH2rA
difficulty: 1
content_type: video_summary
---

# Basic complex analysis | Imaginary and complex numbers | Precalculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=FwuPXchH2rA)*

## Key Concepts
- Representing complex numbers in rectangular form ($a + bi$)
- Visualizing complex numbers using the Argand diagram (complex plane)
- Converting between rectangular form and polar/exponential form
- Calculating the modulus (magnitude) and argument (angle) of a complex number
- Euler's formula and the exponential form of complex numbers

## Definitions
- **Complex Number**: A number of the form $z = a + bi$, where $a$ and $b$ are real numbers, and $i$ is the imaginary unit ($i^2 = -1$)
- **Real Part**: The $a$ in $z = a + bi$, denoted $\text{Re}(z)$
- **Imaginary Part**: The $b$ in $z = a + bi$, denoted $\text{Im}(z)$
- **Argand Diagram**: A coordinate plane where the horizontal axis represents the real part and the vertical axis represents the imaginary part of a complex number
- **Modulus (Magnitude)**: The distance from the origin to the point representing the complex number, given by $|z| = r = \sqrt{a^2 + b^2}$
- **Argument**: The angle $\phi$ between the positive real axis and the line segment from the origin to the point, satisfying $\tan(\phi) = \frac{b}{a}$
- **Euler's Formula**: $e^{i\phi} = \cos\phi + i\sin\phi$

## Examples & Steps
**Example: Convert $z = \frac{\sqrt{3}}{2} + \frac{1}{2}i$ to polar/exponential form**

1. **Calculate the modulus (r):**
   \[
   r = \sqrt{\left(\frac{\sqrt{3}}{2}\right)^2 + \left(\frac{1}{2}\right)^2} = \sqrt{\frac{3}{4} + \frac{1}{4}} = \sqrt{1} = 1
   \]

2. **Calculate the argument ($\phi$):**
   \[
   \tan\phi = \frac{b}{a} = \frac{1/2}{\sqrt{3}/2} = \frac{1}{\sqrt{3}}
   \]
   \[
   \phi = \arctan\left(\frac{1}{\sqrt{3}}\right) = \frac{\pi}{6} \quad \text{(30°, first quadrant)}
   \]

3. **Write in polar/exponential form:**
   - Polar form: $z = r(\cos\phi + i\sin\phi) = 1 \cdot \left(\cos\frac{\pi}{6} + i\sin\frac{\pi}{6}\right)$
   - Exponential form: $z = re^{i\phi} = 1 \cdot e^{i\pi/6}$

**Converting from polar to rectangular form:**
- Given $r$ and $\phi$, the rectangular form is:
  \[
  z = r\cos\phi + (r\sin\phi)i
  \]
- Example: If $r=2$ and $\phi=\frac{\pi}{3}$, then:
  \[
  z = 2\cos\frac{\pi}{3} + 2i\sin\frac{\pi}{3} = 2\cdot\frac{1}{2} + 2i\cdot\frac{\sqrt{3}}{2} = 1 + i\sqrt{3}
  \]

## Summary
This lesson teaches how to represent and visualize complex numbers using both rectangular coordinates ($a + bi$) and polar/exponential form ($re^{i\phi}$). The Argand diagram provides a geometric interpretation where the modulus represents distance from the origin and the argument represents the angle from the real axis. Euler's formula connects these representations, showing that $e^{i\phi} = \cos\phi + i\sin\phi$, which is fundamental for working with complex numbers.