---
topic: precalculus.khan_academy
title: "Parametric equations 2 | Parametric equations and polar coordinates | Precalculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=wToSIQJ2o_8
video_id: wToSIQJ2o_8
difficulty: 2
content_type: video_summary
---

# Parametric equations 2 | Parametric equations and polar coordinates | Precalculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=wToSIQJ2o_8)*

## Key Concepts
- Parametric equations and their graphical representation
- Converting parametric equations to Cartesian form (eliminating the parameter)
- Understanding how parametric equations capture direction and time information
- Setting boundaries on parameter values for real-world applications

## Definitions
- **Parametric Equations**: Equations where x and y coordinates are defined in terms of a third variable (parameter t)
  - Example: $x = f(t)$, $y = g(t)$
- **Parameter (t)**: The independent variable (often representing time) that defines the position along the curve
- **Cartesian Equation**: A single equation relating x and y directly (without a parameter)

## Examples & Steps

### Example 1: Analyzing the Parametric Equations
Given parametric equations:
- $x(t) = 10 + 5t$
- $y(t) = 50 - 5t^2$

**Finding the starting point (t = 0):**
- $x(0) = 10 + 5(0) = 10$
- $y(0) = 50 - 5(0)^2 = 50$
- Point: (10, 50)

**Finding when the object hits the ground (y = 0):**
1. Set $y(t) = 0$: $0 = 50 - 5t^2$
2. Add $5t^2$ to both sides: $5t^2 = 50$
3. Divide by 5: $t^2 = 10$
4. Take square root: $t = \sqrt{10}$ (approximately 3.16)

**Valid parameter range for the car scenario:**
- $0 \leq t \leq \sqrt{10}$ (from cliff edge to ground impact)

### Example 2: Converting Parametric to Cartesian Form
Convert the parametric equations to a single y = f(x) equation:

**Step 1: Solve for t in terms of x**
- $x = 10 + 5t$
- $x - 10 = 5t$
- $t = \frac{x - 10}{5}$

**Step 2: Substitute into y equation**
- $y = 50 - 5t^2$
- $y = 50 - 5\left(\frac{x - 10}{5}\right)^2$
- $y = 50 - 5\left(\frac{(x - 10)^2}{25}\right)$
- $y = 50 - \frac{(x - 10)^2}{5}$

**Step 3: Simplify the equation**
- $y = 50 - \frac{x^2 - 20x + 100}{5}$
- $y = 50 - \frac{x^2}{5} + 4x - 20$
- $y = -\frac{x^2}{5} + 4x + 30$

## Summary
Parametric equations describe curves using a third parameter (often time), providing information about direction and position over time. While parametric equations can be converted to Cartesian form, this conversion loses important information about the direction of motion and timing. Setting appropriate bounds on the parameter is necessary when modeling real-world scenarios like projectile motion.