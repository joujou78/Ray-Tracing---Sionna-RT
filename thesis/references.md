# Master Reference List

Numbered in order of first appearance across the thesis (IEEE style). This file is
shared across all chapters — when a later chapter cites a source for the first
time, append it here as the next number; when a chapter reuses an earlier
source, reuse its existing number. Do not renumber existing entries.

Verification status is tracked so it is visible which entries have been
independently checked against the primary source (not just cited from a prior
project note) versus provided directly by the student.

---

[1] Ericsson, "Ericsson Mobility Report," June 2026. [Online]. Available: https://www.ericsson.com/en/reports-and-papers/mobility-report/reports/june-2026
— Verified via web search of publisher page, 2026-08-16. Used for mobile data traffic / 5G-6G growth motivation figures.

[2] Z. Yun and M. F. Iskander, "Ray Tracing for Radio Propagation Modeling: Principles and Applications," *IEEE Access*, vol. 3, pp. 1089–1100, 2015. doi: 10.1109/ACCESS.2015.2453991.
— Verified via search (ADS abstract, Semantic Scholar, DOI resolves), 2026-08-16.

[3] J. Hoydis et al., "Sionna RT: Differentiable Ray Tracing for Radio Propagation Modeling," arXiv:2303.11103, 2023. Also in *Proc. IEEE ICC Workshops*, 2024.
— Verified via arXiv abstract page search + NVIDIA Research publication page, 2026-08-16.

[4] L. Yu, Y. Miao, J. Zhang, S. Liu, Y. Zhang, and G. Liu, "Road to 6G Digital Twin Networks: Multi-Task Adaptive Ray-Tracing as a Key Enabler," arXiv:2502.14290, 2025.
— Verified via arXiv abstract page search, 2026-08-16.

[5] Ofcom, "UK Radiowave Propagation Measurement Data" (sub-6 GHz propagation measurement dataset), Ofcom Open Data, published 2 Aug. 2019 (data collected 2015–2018 at Boston, London, Merthyr Tydfil, Nottingham, Scar Hill, Southampton; 449/915/1802/2695/3602/5850 MHz).
— Verified via Ofcom open data portal document search, 2026-08-16. THIS is the dataset used throughout the thesis.

[6] 3GPP, "Study on channel model for frequencies from 0.5 to 100 GHz," 3GPP TR 38.901 V18.0.0, May 2024.
— Verified via ETSI/3GPP document search, 2026-08-16. Version confirmed as V18.0.0 (2024-05); a later V19.x exists but V18.0.0 matches the project's stated reference.

[7] A. Manukyan, H. Khachatrian, E. Ghukasyan, and T. P. Raptis, "On the Limitations of Ray-Tracing for Learning-Based RF Tasks in Urban Environments," arXiv:2507.19653, 2025.
— Verified via arXiv abstract + independent search of paper content, 2026-08-16. NOTE: an earlier project note (CLAUDE.md) attributed an unverified "R²~0.5 ceiling at 1.8 GHz" claim to this paper. Two independent searches of its actual content describe Spearman-correlation and k-NN localization evaluation on Rome measurements (0.8–4 GHz) — not an R² path-loss figure. That specific numeric claim is NOT used anywhere in this thesis; this entry is cited only for its actual, confirmed finding (antenna-orientation sensitivity / general fidelity limitations of ray tracing for learning-based tasks).

[8] Environment Agency / Defra, "LIDAR Composite Digital Terrain Model (DTM)" and "Digital Surface Model (DSM)," Defra Data Services Platform. [Online]. Available: https://environment.data.gov.uk/dataset/
— Verified via data.gov.uk / environment.data.gov.uk search, 2026-08-16. Source of UK terrain/vegetation LiDAR used in scene construction.

---

## Pending verification (not yet used in any chapter)
Carried over from the project's CLAUDE.md literature table — to be individually verified before first citation in Chapter 2 (Literature Gap):
- ITU-R P.1411-12 (2019) — dual-slope breakpoint formula
- ITU-R P.833-10 (2021) — vegetation attenuation model
- ITU-R P.2040-2 (2021) — building material EM properties
- Weissberger (1982) — empirical vegetation attenuation model
- NYURay (Ju et al., NYU WIRELESS)
- RadioUNet (Levie et al., 2021)
