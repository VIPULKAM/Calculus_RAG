---
topic: precalculus.khan_academy
title: "Parametric equations 3 | Parametric equations and polar coordinates | Precalculus | Khan Academy"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=57BiI_iD3-U
video_id: 57BiI_iD3-U
difficulty: 2
content_type: video_summary
---

# Parametric equations 3 | Parametric equations and polar coordinates | Precalculus | Khan Academy

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=57BiI_iD3-U)*

## Key Concepts
- Eliminating parameters from parametric equations
- Converting parametric equations to Cartesian form
- Recognizing conic sections from parametric equations
- Understanding the relationship between trigonometric functions and conic sections

## Definitions
- **Parametric Equations**: Equations where variables (x and y) are expressed in terms of a third parameter (t)
  - Example: $x = f(t)$, $y = g(t)$
- **Ellipse**: A conic section defined by the equation $\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1$
- **Trigonometric Identity**: $\cos^2 t + \sin^2 t = 1$ (Pythagorean identity)

## Examples & Steps

### Problem: Eliminate parameter t from the parametric equations
Given: $x = 3\cos t$, $y = 2\sin t$

#### Method 1: Direct substitution (less intuitive)
1. Solve for t in terms of y: $\frac{y}{2} = \sin t$ → $t = \arcsin\left(\frac{y}{2}\right)$
2. Substitute into x equation: $x = 3\cos\left(\arcsin\left(\frac{y}{2}\right)\right)$
3. Result is complex and non-intuitive

#### Method 2: Using trigonometric identity (better approach)
1. Rewrite equations: $\frac{x}{3} = \cos t$, $\frac{y}{2} = \sin t$
2. Apply identity: $\cos^2 t + \sin^2 t = 1$
3. Substitute: $\left(\frac{x}{3}\right)^2 + \left(\frac{y}{2}\right)^2 = 1$
4. Simplify: $\frac{x^2}{9} + \frac{y^2}{4} = 1$

#### Graphing the Ellipse
- Center: (0,0)
- Semi-major axis: 3 (x-direction)
- Semi-minor axis: 2 (y-direction)

#### Parameter Behavior Table
| t | x = 3cos t | y = 2sin t | Point |
|---|---|---|---|
| 0 | 3 | 0 | (3,0) |
| π/2 | 0 | 2 | (0,2) |
| π | -3 | 0 | (-3,0) |

## Summary
This lesson showed how to eliminate parameters from parametric equations using trigonometric identities. By recognizing that $\cos^2 t + \sin^2 t = 1$, we transformed the parametric equations $x = 3\cos t$, $y = 2\sin t$ into the Cartesian form $\frac{x^2}{9} + \frac{y^2}{4} = 1$, which represents an ellipse. This method provides a more intuitive understanding than direct substitution.