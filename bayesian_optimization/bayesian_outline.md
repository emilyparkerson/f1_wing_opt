# Bayesian Outline
## What "I don't know my predicted GP" means (and why that's fine)

You don't *start* with a GP. The GP is **built from data as the algorithm runs**. The whole point of BO is to alternate between gathering data and improving your GP-based predictions. So your concern dissolves once you see the flow.

The mental picture from the textbook:

> We have an expensive objective function f(x). We can't compute its gradient. We can only afford a small number of evaluations. We want to use each evaluation as wisely as possible, so we build a probabilistic model (a GP) that tells us not just what we *think* f looks like, but how *uncertain* we are. We then pick the next x to evaluate by trading off "places that look good" against "places we don't yet understand."

The GP gets refit at every iteration with new data. Initially it knows almost nothing (high uncertainty everywhere). After many evaluations, it knows the response surface well in the regions you've explored.

## The Algorithm at a High Level

```
┌─────────────────────────────────────────────────────────────────┐
│  INITIALIZATION                                                 │
│  - Decide on a kernel (Ch. 18 §"Kernels")                       │
│  - Sample n_init random points in the design space              │
│  - Evaluate f at each (this is the only "blind" phase)          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  MAIN LOOP — repeat until evaluation budget exhausted           │
│                                                                  │
│   1. FIT the GP to all data collected so far                    │
│       - Tune kernel hyperparameters via maximum likelihood       │
│         (Ch. 18 §"Fitting Gaussian Processes")                   │
│                                                                  │
│   2. AT ANY x, GP gives you (μ̂(x), σ̂(x))                         │
│       - μ̂ is the predicted mean (best guess)                    │
│       - σ̂ is the predicted std dev (uncertainty)                │
│                                                                  │
│   3. DEFINE an acquisition function (Ch. 19)                    │
│       - Choices: prediction-based, error-based, LCB, PI, EI      │
│       - We'll use EI                                             │
│                                                                  │
│   4. FIND x* = argmax acquisition(x)                            │
│       - This is a cheap inner optimization (no expensive evals)  │
│                                                                  │
│   5. EVALUATE the true objective: y* = f(x*)                    │
│       - This is the ONE expensive call per iteration             │
│                                                                  │
│   6. APPEND (x*, y*) to your dataset                            │
│                                                                  │
│   7. GO TO 1                                                    │
└─────────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  RETURN the best point ever evaluated                           │
└─────────────────────────────────────────────────────────────────┘
```

## What you need to make this concrete — five questions

The textbook chapters answer these in roughly this order. I'll point you to the relevant section for each.

### Q1: How do I store my data? (Trivial but essential)

You maintain two growing arrays:
- `X` is a matrix where each row is a design point you've evaluated (shape: n × d, where d is dimensions and n grows each iteration)
- `y` is a vector of the objective values at those points (shape: n)

At iteration m, you have m total data points.

### Q2: What's the GP and how do I get (μ̂, σ̂) at a new point? (Ch. 18, §"Gaussian Processes")

A Gaussian process is defined by:

- A **mean function** (usually just 0 — assume the function averages to zero after centering)
- A **kernel function** k(x, x') that measures "similarity" between two design points. The textbook covers several (squared exponential, Matérn, rational quadratic, etc.). For your project, **squared exponential** is the standard choice:

$$k(x, x') = \exp\left(-\frac{\|x - x'\|^2}{2\ell^2}\right)$$

where ℓ is the **lengthscale** — a hyperparameter you need to tune (more on that in Q3).

Given your data (X, y), the GP gives you predictions at any new point x* via:

$$\hat{\mu}(x_*) = k_*^T K^{-1} y$$

$$\hat{\sigma}^2(x_*) = k(x_*, x_*) - k_*^T K^{-1} k_*$$

where:
- K is the n×n matrix of kernel values: K[i,j] = k(xᵢ, xⱼ)
- k* is the n-vector: k*[i] = k(xᵢ, x*)

This is the *prediction* step. The GP is fully specified once you choose the kernel and have data.

### Q3: How do I tune the kernel's hyperparameters? (Ch. 18 §"Fitting Gaussian Processes")

The kernel has one or more hyperparameters (e.g., ℓ for squared exponential). These need to be set, and the textbook explains how: **maximum likelihood estimation**.

You maximize the *log marginal likelihood* of your observed data y given the kernel:

$$\log p(y | X, \theta) = -\frac{1}{2} y^T K^{-1} y - \frac{1}{2} \log |K| - \frac{n}{2} \log 2\pi$$

This is maximized via gradient ascent over the hyperparameters θ (e.g., over log ℓ). In practice, you call `scipy.optimize.minimize` on the negative log marginal likelihood. The textbook gives the gradient formula explicitly if you want to implement it from scratch.

**Practical note:** refit hyperparameters every iteration (or every few iterations to save time). As data grows, the optimal lengthscale typically shrinks because the GP can resolve finer features of the objective.

### Q4: What's the acquisition function? (Ch. 19 §§19.1–19.5)

This is the heart of BO. The textbook walks through five options in increasing sophistication. For your project, I'd use **Expected Improvement (EI)** — it's the de facto standard. Here's how the textbook builds up to it:

| Method | Formula | Behavior |
|---|---|---|
| **Prediction-based (§19.1)** | argmin μ̂(x) | Pure exploitation. No uncertainty. Gets stuck. |
| **Error-based (§19.2)** | argmax σ̂(x) | Pure exploration. Ignores objective. |
| **Lower confidence bound (§19.3)** | argmin (μ̂(x) − α·σ̂(x)) | Trade-off via parameter α. |
| **Probability of improvement (§19.4)** | argmax P(y < y_min) | Chance of beating current best. |
| **Expected improvement (§19.5)** | argmax E[max(y_min − y, 0)] | Expected amount of improvement. ★ |

EI's formula (from algorithm 19.2 in the book):

```python
def expected_improvement(y_min, mu, sigma):
    p_imp = prob_of_improvement(y_min, mu, sigma)   # = Φ((y_min - μ)/σ)
    p_ymin = normal_pdf(y_min, mu, sigma)           # = φ((y_min - μ)/σ) / σ
    return (y_min - mu) * p_imp + sigma**2 * p_ymin
```

(Note: this is the textbook's *minimization* convention. If you're maximizing, flip the signs appropriately. The structure is identical.)

### Q5: How do I find the x that maximizes the acquisition function?

This is the *inner* optimization. The good news: acquisition functions are cheap to evaluate (no MSES calls, just GP predictions), so you can be brute-force:

1. Sample many random points in the design space (e.g., 10,000)
2. Evaluate the acquisition function at each
3. Take the top few and refine each with `scipy.optimize.minimize` (L-BFGS-B, with bounds)
4. Return the best

For low-to-moderate dimensions (your case, ~3-10 D), this works very well.

## Concrete steps to build your own BO

Putting it all together — these are the implementation steps in the order I'd tackle them:

**Phase 1: Get a working GP**
✅1. Implement the kernel function (squared exponential is fine)
✅2. Given training data (X, y), implement `predict(x_star)` returning (μ̂, σ̂) (this is GP)
✅3. Implement hyperparameter optimization (maximize log marginal likelihood)
4. **Test on a 1D toy function** — fit GP to a few points from sin(x), plot mean ± 2σ vs. true function, check that the GP behaves sensibly (matches data exactly at training points, has high uncertainty between)

**Phase 2: Build the acquisition function**
✅5. Implement `expected_improvement(x, gp, y_best)` using the formula above
✅6. **Test it** by evaluating EI across a 1D grid for a fixed GP — verify it's high at promising points, low at well-evaluated points

**Phase 3: Build the loop**
✅7. Implement `optimize_acquisition` (random sampling + local refinement)
8. Wire it all into a loop: initial random sample → fit GP → maximize EI → evaluate → repeat
9. **Test on a benchmark** — Branin (2D), Hartmann (6D). Convergence in tens of iterations is the sign things work

**Phase 4: Hook into your problem**
10. Define your objective(x) function that wraps pymead/MSES (returns score or penalty)
11. Define the design space bounds (alpha, thickness, camber, etc.)
12. Run BO and watch the convergence curve

## What's NOT in the textbook chapter (but matters for you)

A few practical concerns the chapter glosses over but you'll hit in practice:

1. **Failure handling.** When MSES fails to converge, your objective returns NaN or a penalty. The GP can't model NaN — you need to either return a large finite penalty or use a separate "feasibility GP" that classifies designs as feasible/infeasible.

2. **Normalizing y.** GPs assume zero mean. Before fitting, subtract `y.mean()` from your data and divide by `y.std()`. Add them back to predictions.

3. **Numerical stability.** When fitting the GP, the matrix K can be near-singular if two training points are very close. Add a tiny "jitter" to the diagonal (e.g., 1e-6 · I) to stabilize.

4. **Anisotropic lengthscales.** Your design variables have different scales (alpha in degrees, thickness as a fraction). You probably want one lengthscale *per dimension*, not one global lengthscale. This is a small extension to the textbook formula but matters a lot in practice.

5. **Initial sample selection.** The textbook doesn't emphasize this, but Latin Hypercube Sampling (Ch. 13 if I recall) gives much better space coverage than uniform random for initial points.

## TL;DR — your "you don't know the GP" concern

You don't start knowing the GP. You **build it as you go**. At each iteration:

- Take all your evaluations so far → fit a GP (kernel + hyperparameters via max likelihood)
- Use that GP to compute predictions everywhere → maximize acquisition function (EI) → pick next x
- Evaluate the true objective at x → add to your dataset
- Refit the GP next iteration with the additional data point

The GP is a *running model* that gets sharper as you collect more data. The whole point of BO is that the GP doesn't need to be accurate everywhere — just accurate *enough* in the regions worth evaluating.

If you want, next step is for me to walk through implementing the GP from scratch (mapping the textbook equations to working Python), or implementing the EI loop. Tell me which piece feels most uncertain and we'll dig in.

## The big idea
Since each evaluation is expensive, you want to be strategic about where you evaluate next. Random sampling is wasteful. Grid search is impossible (too many points). Local optimizers like Nelder-Mead get stuck in the first valley they find.
BO's insight: build a probabilistic model of f from the points you've already evaluated, then use that model to decide where to evaluate next.
The model isn't just "what do I think f looks like" — it's also "where am I uncertain." That uncertainty is what makes BO smart. It lets you explore (evaluate where you don't know much) and exploit (evaluate where things look promising) in a principled way.

## The two main ingredients
### Ingredient 1: A Gaussian Process (GP)
The GP is your model of f. Given the points you've evaluated so far, the GP tells you, at any new point x:

A predicted value μ̂(x) — "I think f(x) is about this"
A predicted uncertainty σ̂(x) — "but I'm this unsure about it"

Visually, if you sketch the GP:

At points you've already evaluated → mean matches the data, uncertainty is zero
Far from any evaluated point → mean defaults to some prior (often zero), uncertainty is high
Between evaluated points → mean smoothly interpolates, uncertainty is moderate

You can think of it as a "best guess plus error bars" function over the whole design space, that updates as you collect more data.

### Ingredient 2: An acquisition function
This is the rule that picks where to evaluate next. It takes the GP (mean + uncertainty everywhere) and returns a single number for each candidate x: "how desirable is it to evaluate here?"
The most common one is Expected Improvement (EI): "if I evaluate at x, what's the expected amount by which I'll beat my current best?" It naturally balances:

High μ̂ regions (looks promising → high EI) — exploitation
High σ̂ regions (could be surprising → high EI) — exploration

So EI is high either where things look good or where you don't know yet. Both are worth investigating.



RUNNER SCRIPT (run_bo.py)
                          │
                          │ creates
                          ▼
                  BayesianOptimizer
                          │
                          │ .run() loop:
                          ▼
       ┌──────────────────┴───────────────────┐
       │                                       │
       ▼                                       ▼
  fit_hyperparameters(X, y)         optimize_acquisition(predict, y_best, bounds)
       │                                       │
       │ uses                                   │ uses
       ▼                                       ▼
  sq_exp_kernel                       expected_improvement
                                                │
                                                │ uses
                                                ▼
                                          gp_predict(X, y, X_new)
                                                │
                                                │ uses
                                                ▼
                                          sq_exp_kernel