## ETF Strategy Optimization - Open Questions

### [ETF Strategy Optimization - Revised Plan] - 2026-03-08

- [ ] Should we implement parameter optimization (grid search, genetic algorithm) or leave it manual? — Affects backtest UI scope and backend computational complexity
- [ ] Do we need a database to store backtest results for historical comparison? — Affects data persistence architecture
- [ ] Should strategy parameters be user-specific (stored per user) or global defaults? — Affects API design and storage requirements
- [ ] What is the exact timeline for Phase 2 and Phase 3 deprecation (dates vs. versions)? — Affects migration planning
- [ ] Do we need real-time paper trading integration? — Out of scope for this plan but affects future roadmap

### [ETF Strategy Optimization] - 2026-03-08 (Original)

- [ ] What is the deprecation timeline for the risk_preference API field? — Affects Phase 3 implementation and migration planning (superseded by revised 3-phase plan)
