---
topic: precalculus.khan_academy
title: "Exponential Growth"
source: Khan Academy
source_url: https://www.youtube.com/watch?v=JWfTckls59k
video_id: JWfTckls59k
difficulty: 2
content_type: video_summary
---

# Exponential Growth

*Source: [Khan Academy Video](https://www.youtube.com/watch?v=JWfTckls59k)*

## Key Concepts
- Exponential growth models
- Solving for constants in exponential functions using initial conditions
- Finding growth rates using derivatives
- Relationship between exponential and logarithmic functions

## Definitions
- **Exponential Growth**: Growth proportional to current size, modeled by $P(t) = P_0 e^{kt}$
  - $P(t)$: population at time $t$
  - $P_0$: initial population ($P_0 = P(0)$)
  - $k$: growth rate constant
  - $t$: time

- **Natural Logarithm**: Inverse function of $e^x$, denoted $\ln(x)$
  - Property: $e^{\ln(x)} = x$

## Examples & Steps

### Problem Setup
A bacteria culture starts with 100 cells and grows to 420 cells after 1 hour.

**Part A: Find expression for bacteria after t hours**

1. Start with general exponential model:
   $$b(t) = b_0 e^{kt}$$

2. Use initial condition $b(0) = 100$:
   $$b(0) = 100e^{k\cdot0} = 100 \Rightarrow b_0 = 100$$

3. Use condition $b(1) = 420$:
   $$420 = 100e^{k}$$
   $$4.2 = e^{k}$$
   $$k = \ln(4.2)$$

4. Final expression:
   $$b(t) = 100e^{\ln(4.2)t}$$

**Part B: Find bacteria after 3 hours**

1. Substitute $t = 3$:
   $$b(3) = 100e^{\ln(4.2)\cdot3}$$

2. Simplify using $e^{\ln(4.2)} = 4.2$:
   $$b(3) = 100(4.2)^3$$

**Part C: Find growth rate after 3 hours**

1. Differentiate $b(t)$:
   $$b'(t) = 100\cdot\ln(4.2)\cdot e^{\ln(4.2)t}$$

2. Evaluate at $t = 3$:
   $$b'(3) = 100\ln(4.2)\cdot e^{\ln(4.2)\cdot3}$$
   $$b'(3) = 100\ln(4.2)\cdot(4.2)^3$$

## Summary
This lesson demonstrates how to model exponential growth using $P(t) = P_0 e^{kt}$. By using initial conditions and data points, we can solve for the constants $P_0$ and $k$. The growth rate at any time is found by differentiating the exponential function, showing that the rate itself grows exponentially.