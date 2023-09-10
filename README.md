# Fourier series animations from SVG files

This project provides scripts to generate Fourier series animations from SVG
files.

<p align="center"><img src=./assets/fourier.gif></p>

⚠️ The SVG file has to be made of only one path

## Setup

- Install:
  ```bash
  git clone https://github.com/mxmpl/fourier-svg
  cd fourier
  pip install .
  ```
- Usage:
    ```bash
    fourier $SVG_PATH
    ```

## How does it work?

A SVG file is a XML file where each entry describe different
[paths](https://www.w3.org/TR/SVG/paths.html) to draw, where each path is made of
of lines, elliptical arcs or Bézier curves. A path can be described as a parametric
curve $\gamma : [0, 1] \rightarrow  \mathbb{C}$ where $\gamma(0)$ is the first
point  of the curve and $\gamma(1)$ is the last.

If the path is not too irregular[^1] we can express it as a Fourier Series:

$$
    \forall t \in [0, 1], \gamma(t) = \sum_{n \in \mathbb{Z}} c_n e^{2 i \pi n t}
$$
with $(c_n)_{n \in \mathbb{Z}}$ the Fourier coefficients:

$$
  \forall n \in \mathbb{Z}, c_n = \int_{0}^{1} \gamma(t) e^{-2i\pi n t} \mathrm{d}t \in \mathbb{C}
$$

Now we only need to choose a number $N$ of coefficients to keep, and compute numerically the $c_n$ for $-N/2 \leq n \leq N/2$. At time $t$, using the first equation, by computing only the partial sum we obtain an approximation of $\gamma(t)$ and therefore a point on the curve. This is done for a given number of times in $[0,1]$, resulting in the final figure.

Regarding the animation with circles, it's important to note that each term of the Fourier series corresponds to a complex number with a fixed magnitude. Over time, we follow a circle whose radius is the Fourier coefficient $c_n$ at frequency $n$. To create the animation, we add the complex terms together ordered by magnitude.

[^1]: If $\gamma$ is piecewise $C^1$ there is pointwise convergence, and if $\gamma$ is a function of $L^2([0,1], \mathbb{C})$ there is $L^2$ convergence.