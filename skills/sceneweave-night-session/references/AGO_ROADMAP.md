# AGO — full evidence-driven Gaussian lifecycle and map resource controller

## Mission

AGO replaces the default Gaussian *strategy* (ADC, MCMC relocation, pruning, resets, fixed optimization schedule and residency decisions) in a validated external-strategy mode. Adam or another numerical optimizer may remain a low-level primitive. One policy owns mutation decisions; no hidden ADC/MCMC changes run in parallel. Keep existing strategies as switchable baselines until AGO is validated. The objective is better verified and provisional map information, at equal time/evidence/memory, not more optimizer steps or greater splat count.

## Existing engine foundation (as checked 25 Nov 2026)

VkSplat PR #19: arbitrary active sets, telemetry, native differentiable depth loss. PR #20: GPU compaction. PR #21 (`f4180f94`): GPU exact-count selection (`select_ago_exact_k_gpu`), and temporal depth reprojection (`reproject_temporal_depth_gpu`). Exact count does not imply an exact globally sorted top-K: audit histogram boundary/tie behavior, visibility and eligibility. The Python bindings also expose group state, sparse anchors/re-anchoring, append preserving optimizer, retraction/compaction, persistent UIDs, snapshots, training batches and budget APIs. Do not reimplement existing primitives. Local night branches are not verified by this document. Inspect real APIs and engine strategy ownership before coding.

## Architecture

- `AGOController`: policy and resource budgets, causal actions, priority/urgency, learned/calibrated marginal utility and cost, current deadlines, fairness and starvation prevention. Default fast path uses resident GPU summaries, not Python per-Gaussian loops.
- `SpatialMapIndex`: building -> floor -> room/submap -> tile or octree block -> surfel/point Gaussian UIDs. Room labels are uncertain, not hard immutable ownership; maintain cross-boundary halos/portals. Use stable local submap coordinate systems, partition revisions and generation counters. Shared elements have one authoritative owner.
- `EvidenceHeatmap`: spatial multi-channel quality-deficit and opportunity map; per tile and per visible Gaussian reduce independent measured depth residuals, reprojection/normal disagreement, RGB residual/gradient frequency, visibility/coverage, support count and view-direction diversity, expected gain, reliability, blur and motion, structural contradiction, age, occupancy/free-space conflicts, task importance and resource cost. Distinguish no evidence (request observation) from detailed measured evidence but missing map detail (allocate representation) and high residual due to bad pose/depth (fix sensing/SLAM before densifying).
- `ActionPlanner`: choose from `refine(params, ids, views)`, `insert`, `clone`, `split`, `merge`, `prune`, `relocate`, `reanchor`, `retract`, `freeze`, `reopen`, `change_lod`, `repartition`, `prefetch`, `evict`, `replay`, `idle`, and request evidence/pose correction. Separate position, rotation/scale, opacity, SH/appearance and structure operations. Use action preconditions, bounded operation batches, stable UID lineage, explicit optimizer-moment handling, transactional rollback and generation checks. GPU kernels execute fast local actions; slower CPU policy chooses coarse budgets and jobs; asynchronous I/O is outside the live critical path.
- `ResidencyManager`: separate residency, rendering availability, optimization activity, and evidence status. GPU hot = actively optimized or visible; GPU resident but passive = renderable without optimizer updates; RAM warm = full recoverable chunk; disk cold = durable chunk with coarse proxy and metadata. Never equate eviction with forgetting, prune with cache-out, or low LOD with physical verification. Retain verified safety geometry independent of Gaussian rendering residency. Cache optimizer moments, UIDs, provenance, transform/version, SH, covariance, anchors and keyframe references; checksums, atomic save, bounded queues, prefetch and hysteresis. On unified memory, GPU and RAM use the same physical pool: measure real GTT/RSS and transfer/synchronization costs, not assumed VRAM savings.
- `IntegrationBus`: SceneWeave Evidence provides measured vs prior lineage, contradictions and surface support; Sense supplies uncertainty, source dependencies, valid depth and noise; SLAM supplies pose covariance, local submap transforms, motion and pose-graph revisions; Teach supplies reusable templates with confidence; MST supplies provisional object hypotheses. Prevent circular evidence and unsupported promotions. SLAM revisions invalidate stale world-space cues, re-anchor/reproject affected regions and reset affected optimizer moments deliberately. A cached region must not reappear in outdated coordinates.

## Action selection and metrics

Use calibrated expected benefit/cost per feasible action with multiple quality channels (geometry, calibrated predictive log-score, visual quality, task utility, correction), separate hard safety/provenance and resource constraints, and long-horizon value for prefetch/eviction. Report realized gains and prediction calibration, not just first-order training loss. Use causal replay holdbacks and independent offline evaluation. Prioritize contradiction deadlines, then budgeted utility; reserve minimum exploration/refresh capacity and enforce hysteresis, cooldowns, no starvation, and bounded queue lengths. A zero-information action can idle; no empty active-set fallback that optimizes frozen states unexpectedly.

Spatial detail: compare sensor-supported recoverable bandwidth/detail (sampling density, noise, view angle, blur, range and multiview support) against map-rendered metric depth/normal and RGB frequency deficits. Use geometry refinement only for reliable geometric detail and SH/color updates for appearance-only detail. Never densify on noise, pose misalignment, motion blur or unverified depth. LoD must support smooth rendering, independent coarse/fine quality targets, consistent geometry and opacity (no double counting), and local merge/split decisions. Nearby, task-relevant regions may receive detail earlier, while remote regions retain coarse context and their full representation in cache.

## Phased research plan

AGO-0 ownership / ABI: inventory all default strategy writes (ADC/MCMC, opacity reset, growth/prune, masks, freeze), introduce an explicit external-strategy switch with hidden-mutation invariant; implement action journal, UID/version/moment rules; verify mode parity with a fixed uniform policy.

AGO-1 regional deficit map: build sparse tile heatmap from existing native telemetry and physical residuals, use region-specific visibility and causality; offline counterfactual calibration of utility; show heatmap RGB/depth/normal overlays and action targets. Compare with random and uniform at equal time, actual subset size and evidence. Start with existing exact-K API, not another selector rewrite.

AGO-2 closed-loop refinement: per-group parameter masks and batched actions; select geometry vs appearance; prove inactive parameters/moments unchanged; profile total rasterization/backward/optimizer path. A GPU micro-kernel speedup alone is insufficient.

AGO-3 capacity redistribution: under hard budget, compare insertion/split/merge/relocation/prune to ADC and MCMC with equal actual counts and resource budgets; test deficit-directed density rather than fixed growth; use physically supported corrections and distinguish evidence from speculative capacity.

AGO-4 partitioning + LoD: start with immutable tile ownership, then room/submap hierarchy and coarse/fine levels; measure local detail and stability on two-room and revisits. Use submap transforms and cross-boundary continuity. Rendering LoD alone is not enough; map construction must allocate density and optimization adaptively.

AGO-5 tiered residency: chunk serialization round-trip incl. moments/UIDs/provenance, RAM cache, disk cache, visibility/task-aware activation and prefetch, loop-closure revisions. Test repeated room visits, capacity pressure and cache thrashing. Report p50/p95/p99 restoration and map-publication delay, cache hit/miss, bytes transferred, peak physical memory and reconstruction retention.

AGO-6 full replacement: combine only validated modules, benchmark bounded compute and map growth on longer multi-room/building trajectories; compare default ADC, MCMC, uniform fixed budget and relevant hierarchical/submap baselines. Keep sealed scoring separate from development.

## Initial implementation priorities

1. Explicit strategy ownership plus action API/journal; no hidden engine mutations.
2. Spatial heatmap, evidence/sense/SLAM features, region utility counterfactuals using meaningful partially reconstructed maps.
3. One density redistribution action under a hard cap, and one selective parameter-update path. Use exact-count selection and same-sized random controls.
4. Prototype partition metadata and lossless chunk round-trip on CPU; only then port performance-critical GPU residency/LOD operations.

For each stage compare complete TTQ/ETQ curves, independently measured 5/10/20 cm coverage, surface precision/recall, actual RVIG, contradiction correction, task utility and compute/memory. Initial engineering targets (not achieved): resident fast selection/action planning ~1 ms p95 on current dev scale if practical, scheduling overhead <5–10%, reactive correction within the next eligible frame subject to physical evidence, bounded frame p95/p99 and deadline misses (66 ms existing target; 33 ms stretch). Use S54 uninterrupted timing and test >=200-frame live-arrival traces with real revisits. Measure overall performance not individual kernel latency only.

## Related work to benchmark, not novelty claims

- 3DGS-MCMC (NeurIPS 2024): https://3dgs-mcmc.github.io/ — relocation and adaptive population baseline.
- Octree-GS: https://city-super.github.io/octree-gs/ — multi-resolution anchor/grow-prune baseline.
- Hierarchical 3D Gaussians (SIGGRAPH 2024): https://repo-sam.inria.fr/fungraph/hierarchical-3d-gaussians/ — chunked hierarchy and rendering LoD baseline.

The distinctive hypothesis is online evidence-conditioned joint allocation of computation, Gaussian capacity, spatial detail and residency for robotics. Do not claim the combination is novel until a wider related-work review and controlled baselines support that claim.
