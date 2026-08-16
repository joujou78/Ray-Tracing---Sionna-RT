# Chapter 1 — Research Problem

## 1.1 Background and Motivation

Global mobile data traffic continues to grow rapidly, with 5G now carrying roughly half of all mobile network traffic worldwide and adoption projected to keep rising sharply toward the end of the decade [1]. This growth is driving denser urban deployments and pushing operators toward higher-frequency mid-bands, both of which increase the importance of accurately predicting how radio signals propagate through complex, cluttered environments before a network is built [1].

Two broad families of propagation models are used for this purpose. Empirical models are computationally cheap and require little environmental detail, but they average over large classes of environments and cannot capture site-specific structural variation such as individual building layouts or material composition [2]. Deterministic ray tracing, in contrast, models propagation through explicit interactions — reflection, diffraction, and scattering — with a three-dimensional representation of the environment, and is capable of substantially higher site-specific accuracy at the cost of requiring detailed geometric and material input and significantly greater computational load [2]. This accuracy–cost trade-off has historically limited the use of ray tracing to small, carefully surveyed sites.

Recent GPU-accelerated, differentiable ray tracers — most notably Sionna RT — have narrowed this gap by making large-scale, repeated ray-tracing evaluation computationally tractable and by allowing model parameters such as material permittivity and conductivity to be calibrated through gradient-based optimization rather than manual tuning [3]. This capability is a key enabler behind the broader push toward network digital twins for 6G, in which a continuously updated ray-tracing representation of the physical network is used for planning, prediction, and optimization [4]. Realizing this vision, however, depends on first establishing how accurately a calibrated, purely geometric ray tracer can reproduce real, measured propagation behaviour across the frequency bands and environment types a future network must operate in — dense urban and rural, sub-1 GHz and mid-band alike.

## 1.2 Problem Statement

Validating a ray tracer against real measurements at city scale requires three things that are individually well understood but rarely combined and reported together in the open literature: (i) a geometrically accurate 3D scene — buildings, terrain, and vegetation — built from real survey data rather than idealized geometry; (ii) a calibration procedure that fits material electromagnetic properties to measurements rather than assuming generic textbook values; and (iii) a measurement dataset spanning multiple frequencies and site types against which the calibrated model's accuracy, and its limits, can be quantified. The Ofcom 2018 UK propagation measurement campaign provides exactly such a multi-frequency, multi-site dataset, having recorded over eight million path-loss measurements across six frequencies (449 MHz–5850 MHz) at seven UK sites of varying morphology [5].

Even with such a dataset and a capable ray tracer, several specific engineering difficulties remain open. First, surface-based ray tracers compute electromagnetic interactions only at discrete surface intersections, which makes volumetric phenomena — most importantly attenuation through tree canopies — difficult to represent physically, particularly as wavelength shrinks relative to the scattering structures involved. Second, coherent summation of multipath components becomes increasingly sensitive to small geometric errors as frequency increases, so the choice between coherent and incoherent combination is not fixed but appears to shift with wavelength and scene complexity. Third, standard reference propagation models such as 3GPP TR 38.901 assume single-slope or dual-slope behaviour with a breakpoint distance set by transmitter and receiver heights and frequency [6], and calibrating a ray tracer across data that spans this breakpoint risks mixing two distinct physical regimes into a single fit. Finally, recent independent analysis of Sionna-based ray tracing against real urban measurements in Rome has shown that simulation fidelity is highly sensitive to factors such as antenna placement and orientation, and that ray-tracing accuracy against ground truth cannot simply be assumed without site-specific validation [7].

The engineering challenge this thesis addresses is therefore to construct, calibrate, and evaluate a Sionna RT-based propagation model against the Ofcom 2018 measurements across four frequencies (915 MHz, 1802 MHz, 2695 MHz, 3602 MHz) at both dense urban and rural sites, in order to quantify prediction accuracy, identify the accuracy ceiling ("physics floor") achievable through geometry-and-material calibration alone, and characterise the specific failure modes — vegetation, dual-slope mixing, and coherent-interference collapse — that limit it.

## 1.3 Aim and Objectives

**Aim:** To quantify how accurately a calibrated, purely geometric ray tracer (Sionna RT 2.0) predicts real-world path loss across a range of sub-6 GHz frequencies and environment types, and to identify the physical and methodological limits of that accuracy.

**Objectives:**
1. Construct 3D propagation scenes for dense urban (Nottingham, London) and rural (Scar Hill) sites using UK Environment Agency LiDAR terrain and vegetation canopy data [8] combined with OpenStreetMap building and infrastructure data.
2. Develop and apply a multi-phase calibration pipeline that fits building and ground material electromagnetic properties (permittivity, conductivity, scattering coefficient) to measured path loss at each site and frequency.
3. Quantify prediction accuracy (R², RMSE, bias) of the calibrated model against Ofcom 2018 measurements at 915 MHz, 1802 MHz, 2695 MHz, and 3602 MHz in Nottingham, and at 915 MHz in London and at the rural Scar Hill site.
4. Characterise frequency-dependent failure modes, specifically: vegetation attenuation modelling as wavelength approaches vegetation feature scale, the dual-slope line-of-sight/non-line-of-sight breakpoint, and the stability of coherent versus incoherent multipath summation.
5. Compare urban and rural generalisation of the calibrated approach and identify the dominant source of residual error in each case (e.g., terrain resolution versus vegetation representation).

## 1.4 Research Questions

- **RQ1:** How does the prediction accuracy of a calibrated Sionna RT model vary with frequency (915–3602 MHz) in a dense urban environment?
- **RQ2:** What scene-representation and calibration choices are required to model vegetation attenuation realistically as wavelength decreases toward the scale of vegetation structures?
- **RQ3:** What is the achievable accuracy ceiling of pure geometry-and-material calibration, without learned or statistical residual correction, and where does it fall short of measured behaviour?
- **RQ4:** How does model accuracy generalise from a dense urban site to a rural, terrain-dominated site using the same calibration methodology?

## 1.5 Scope and Limitations

This thesis is scoped to the Sionna RT 2.0 surface-based ray tracer [3], applied to four Ofcom 2018 measurement sites (Nottingham, London, Scar Hill) at four frequencies between 915 MHz and 3602 MHz [5], using UK Environment Agency LiDAR [8] and OpenStreetMap data for scene construction. It is explicitly limited to purely geometric ray tracing with classical (non-learned) material calibration; hybrid ray-tracing/neural residual correction approaches are identified as a promising direction but fall outside the scope of the experimental work presented here. Millimetre-wave and above-6 GHz bands, indoor propagation, and non-UK sites are not evaluated.

## 1.6 Significance and Contribution

This work contributes an empirically validated, multi-frequency comparison of ray-tracing accuracy against real, multi-site measurement data — a combination that is documented only sparsely in the open literature — together with a reproducible scene-construction and calibration pipeline built from open UK geospatial data [8]. In establishing where purely geometric calibration reaches its accuracy ceiling and which failure modes dominate at each frequency, this thesis provides an evidence base directly relevant to the accuracy expectations of ray-tracing-based digital twins now being proposed for 6G network planning [4].

## 1.7 Thesis Structure Overview

Figure 1 illustrates the overall research framework, linking the problem definition, literature gap, proposed method, implementation, and validation stages that guide the development of this thesis. Each stage corresponds to a chapter, ensuring a logical progression from theoretical foundations to practical experimentation and final conclusions:

- **Chapter 1 – Research Problem** — Defines the engineering challenge, practical need, and scientific motivation underlying urban wireless propagation modeling.
- **Chapter 2 – Literature Gap** — Reviews existing propagation models, identifies missing knowledge, and highlights unresolved technical issues.
- **Chapter 3 – Proposed Method** — Presents the deterministic Ray Tracing approach, simulation framework, and scene generation methodology using EA LiDAR Defra and OpenStreetMap data.
- **Chapter 4 – Implementation** — Details system modeling, simulation setup, data collection, and tool configuration within the Sionna RT environment.
- **Chapter 5 – Results & Validation** — Analyzes radio environmental maps, evaluates propagation metrics, and compares results with classical models.
- **Chapter 6 – Conclusions** — Summarizes findings, discusses limitations, and outlines future directions in differentiable Ray Tracing and digital twin applications.

This structure ensures methodological transparency, academic rigor, and practical relevance while establishing a comprehensive framework for advanced urban wireless propagation analysis.

---

*References for this chapter are numbered [1]–[8]; see `references.md` for the full, verified reference list shared across all chapters.*
