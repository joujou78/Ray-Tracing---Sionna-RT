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

[9] M. Hata, "Empirical Formula for Propagation Loss in Land Mobile Radio Services," *IEEE Trans. Veh. Technol.*, vol. VT-29, no. 3, pp. 317–325, Aug. 1980. doi: 10.1109/T-VT.1980.23859.
— Verified via search (DOI, multiple citation-index confirmations), 2026-08-16. The canonical Okumura–Hata model reference.

[10] COST Action 231, "Digital Mobile Radio Towards Future Generation Systems," COST 231 Final Report, European Commission, EUR 18957, 1999. ISBN 9789282854167.
— Verified via search (Aalborg Univ. research portal, WorldCat, Rutgers WINLAB hosted copy), 2026-08-16.

[11] H. T. Friis, "A Note on a Simple Transmission Formula," *Proc. IRE*, vol. 34, no. 5, pp. 254–256, 1946. doi: 10.1109/JRPROC.1946.234568.
— Verified via search (DOI, Semantic Scholar), 2026-08-16.

[12] W. Jakob, S. Speierer, N. Roussel, and D. Vicini, "Dr.Jit: A Just-In-Time Compiler for Differentiable Rendering," *ACM Trans. Graph. (Proc. SIGGRAPH)*, vol. 41, no. 4, 2022. arXiv:2202.01284.
— Verified via arXiv abstract + ACM/SIGGRAPH history page search, 2026-08-16.

[13] W. Jakob et al., "Mitsuba 3: A Retargetable Forward and Inverse Renderer," EPFL / Mitsuba Renderer project. [Online]. Available: https://github.com/mitsuba-renderer/mitsuba3
— Verified via GitHub README + CG Channel coverage search, 2026-08-16. No standalone academic paper was found distinct from the Dr.Jit paper [12]; cited as the software project itself.

[14] M. Pesko, T. Javornik, A. Košir, M. Štular, and M. Mohorčič, "Radio Environment Maps: The Survey of Construction Methods," *KSII Trans. Internet Inf. Syst.*, vol. 8, no. 11, pp. 3789–3809, Nov. 2014. doi: 10.3837/tiis.2014.11.008.
— Verified via search (Korea Science / journal page, DOI), 2026-08-16.

[15] ITU-R, "Propagation data and prediction methods for the planning of short-range outdoor radiocommunication systems and radio local area networks in the frequency range 300 MHz to 100 GHz," Recommendation ITU-R P.1411-10, Aug. 2019.
— Verified via ITU.int document search, 2026-08-16. **CORRECTED from CLAUDE.md**, which cited this as "P.1411-12 (2019)" — no P.1411-12 was found; P.1411-10 is the version actually published in August 2019 (P.1411-11 followed in Sept. 2021, P.1411-13 in Sept. 2025). The version number in the project notes appears to have been an error; the year was correct.

[16] ITU-R, "Attenuation in vegetation," Recommendation ITU-R P.833-10, Sept. 2021.
— Verified via ITU.int document search, 2026-08-16. Matches CLAUDE.md citation exactly.

[17] ITU-R, "Effects of building materials and structures on radiowave propagation above about 100 MHz," Recommendation ITU-R P.2040-2, Sept. 2021.
— Verified via ITU.int document search, 2026-08-16. Matches CLAUDE.md citation exactly.

[18] M. A. Weissberger, "An Initial Critical Summary of Models for Predicting the Attenuation of Radio Waves by Trees," ESD-TR-81-101, EMC Analysis Center, Annapolis, MD, 1982.
— Verified via search (Wikipedia "Weissberger's model" + secondary literature citing the report), 2026-08-16.

[19] O. Kanhere, H. Poddar, and T. S. Rappaport, "Calibration of NYURay for Ray Tracing using 28, 73, and 142 GHz Channel Measurements Conducted in Indoor, Outdoor, and Factory Scenarios," arXiv:2410.03104, 2024 (accepted, IEEE Trans. Antennas Propag.).
— Verified via arXiv abstract + ResearchGate, 2026-08-16. **CORRECTED from CLAUDE.md**, which attributed NYURay to "Ju et al." — the actual calibration paper's authors are Kanhere, Poddar, and Rappaport (S. Ju appears as a co-author on a related NYU measurement-campaign paper, not this calibration paper).

[20] R. Levie, C. Yapar, G. Kutyniok, and G. Caire, "RadioUNet: Fast Radio Map Estimation With Convolutional Neural Networks," *IEEE Trans. Wireless Commun.*, vol. 20, no. 6, pp. 4001–4015, 2021.
— Verified via search (publication details consistent across multiple sources), 2026-08-16. Matches CLAUDE.md citation.

[21] J. Hoydis, F. Aït Aoudia, S. Cammerer, F. Euchner, M. Nimier-David, S. ten Brink, and A. Keller, "Learning Radio Environments by Differentiable Ray Tracing," arXiv:2311.18558, 2023 (IEEE Trans. Machine Learning in Communications and Networking, 2024).
— Verified via arXiv abstract + IEEE Xplore listing, 2026-08-16. This is the paper CLAUDE.md referred to as "NVLabs diff-rt-calibration (Hoydis et al.)".

[22] ITU-R, "Effects of building materials and structures on radiowave propagation above about 100 MHz," Recommendation ITU-R P.2040-1, Jul. 2015.
— Recommendation's existence and approval date verified via ITU.int / Accuris Standards Store search, 2026-08-16. **UNVERIFIED CONTENT**: the specific numeric reflection-loss values commonly quoted alongside this recommendation (brick ≈ 8 dB, glass ≈ 4 dB, concrete ≈ 10–12 dB at 2.4 GHz) could not be confirmed against the primary document or any secondary source in this session's searches. Do not cite these figures as ITU-R P.2040-1 values without pulling the actual table from the PDF first — see caution note in Chapter 2, Section 2.1.3.

[23] R. G. Kouyoumjian and P. H. Pathak, "A Uniform Geometrical Theory of Diffraction for an Edge in a Perfectly Conducting Surface," *Proc. IEEE*, vol. 62, no. 11, pp. 1448–1461, Nov. 1974.
— Verified via search (ADS abstract, IEEE Xplore listing, multiple citation confirmations), 2026-08-16. The canonical Uniform Theory of Diffraction (UTD) reference.

---

[24] D. Chizhik, J. Ling, P. Wolniansky, R. Valenzuela, N. Costa, and K. Huber, "Multiple-Input-Multiple-Output Measurements and Modeling in Manhattan," *IEEE J. Sel. Areas Commun.*, vol. 21, no. 3, pp. 321–331, Apr. 2003. doi: 10.1109/JSAC.2003.809457.
— Verified via search (DOI, dblp, Nokia Bell Labs author pages), 2026-08-16. **CORRECTED year**: a draft passage cited "Chizhik et al. (2004)" — the actual publication is 2003.

[25] T. S. Rappaport, G. R. MacCartney, M. K. Samimi, and S. Sun, "Wideband Millimeter-Wave Propagation Measurements and Channel Models for Future Wireless Communication System Design," *IEEE Trans. Commun.*, vol. 63, no. 9, pp. 3029–3056, Sept. 2015.
— Verified via search (publication details consistent across multiple sources), 2026-08-16. Matches the "Rappaport et al. (2015), mmWave sensitivity to urban materials" description in the draft passage.

[26] University of Bologna (author name not confirmed — WebFetch to amslaurea.unibo.it is network-blocked in this session), "High Resolution Radio Environmental Maps Using Sionna Ray Tracing: The Case Study of Bologna," undergraduate/master's thesis, AMS Laurea repository, eprint 35655, Jul. 2025. Available: https://amslaurea.unibo.it/id/eprint/35655/
— Existence, abstract content, and July 2025 date verified via search (ResearchGate listing, repository URL). **Author name not yet confirmed** — student should pull this directly from the repository page before final citation. This is the source of the Bologna/Blender/CPU-only passage originally pasted into this chapter; it is now cited properly as a related work (Section 2.2/2.6) rather than reused as this thesis's own methodology text.

---

[27] V. Degli-Esposti, F. Fuschini, E. M. Vitucci, and G. Falciasecca, "Measurement and Modelling of Scattering From Buildings," *IEEE Trans. Antennas Propag.*, vol. 55, no. 1, pp. 143–153, Jan. 2007. doi: 10.1109/TAP.2006.888422.
— Verified via search (DOI, multiple citation-index confirmations), 2026-08-18. The canonical Effective Roughness / directive scattering model reference underlying the scattering coefficient *S* used in Sionna RT's `RadioMaterial` and in this project's material calibration.

---

## Not used — could not verify, do not cite
"Loyka & Kouki (2008)," described in a draft passage as covering "polarization and multipath modeling accuracy" in ray tracing. The only Loyka & Kouki publication found is S. L. Loyka and A. B. Kouki, "Using Two-Ray Multipath Model for Microwave Link Budget Analysis," *IEEE Antennas Propag. Mag.*, vol. 43, pp. 31–36, 2001 (plus a related 2001 CCECE conference paper on fade-depth prediction) — a different year (2001, not 2008) and a narrower topic (two-ray fade depth, not general polarization/multipath RT accuracy). Do not cite this as "Loyka & Kouki (2008)" without locating the specific paper the draft actually intended.

## Pending verification (not yet used in any chapter)
The specific ITU-R P.2040-1 material reflection-loss values [22] still need primary-source confirmation before final submission. Hardware/VM specs for Chapter 2 Section 2.5.2 (CPU core count, RAM, VM/cluster type) are pending from the student — only the GPU (Tesla V100-SXM2-16GB, confirmed via `sionna019_calibration.ipynb`) is verified so far.
