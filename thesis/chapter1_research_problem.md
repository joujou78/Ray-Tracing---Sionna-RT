# Chapter 1 — Introduction

This chapter introduces the research problem addressed by this thesis. It presents the urban wireless propagation context, states the problem and research gap, introduces Ray Tracing as the proposed solution, describes the selected study areas, and sets out the research questions and objectives that guide the remainder of the work.

## 1.1 Wireless Communication in the Urban Context

Wireless communication has become a cornerstone of modern urban life, shaping how cities expand, operate, and adapt to technological change. Contemporary urban environments function as interconnected digital ecosystems, supporting technologies such as 5G networks, smart transportation, autonomous mobility, IoT services, and intelligent energy management, driven in large part by continued growth in mobile data demand [1]. Reliable connectivity is therefore not a luxury but a socio-economic necessity.

Propagation in urban areas, however, is highly complex. Dense and irregular structures composed of stone, brick, glass, vegetation, and concrete introduce reflection, diffraction, scattering, penetration losses, and shadowing [2]. These effects generate severe multipath propagation and rapid spatial fluctuations. European cities, with their narrow streets, irregular building layouts, porticoes, arches, and aged construction materials, present particularly difficult conditions: materials such as stone, brick, glass, and concrete interact with electromagnetic waves in distinct ways, producing highly dynamic propagation behaviours that conventional models often fail to capture [2]. Traditional models such as Okumura–Hata [9], Free-Space Path Loss (FSPL) [11], and COST-231 [10] rely on empirical assumptions and coarse spatial resolutions, making them unsuitable for high-precision urban planning (see Section 1.2).

Deterministic, geometry-aware approaches such as Ray Tracing (RT) address these limitations by explicitly modelling electromagnetic interactions with realistic geometries and materials, capturing reflections, diffractions, scattering, and multipath effects and enabling the generation of high-resolution radio environmental maps [2], [14]. This thesis employs NVIDIA's Sionna RT framework, which integrates the Mitsuba 3 rendering engine [13] and the Dr.Jit differentiable just-in-time compiler [12] to provide differentiable Ray Tracing capabilities [3]. Its architecture allows calibration of material properties, antenna configurations, and scene parameters, reducing prediction errors and improving fidelity [3]. The simulations conducted in this thesis are executed in GPU mode, using hardware provided by the university, which the Sionna RT framework is designed to exploit for detailed urban propagation analysis [3].

To address these shortcomings, modern wireless research increasingly adopts deterministic, geometry-aware techniques that explicitly model the physical environment. Among these, radio environmental maps have emerged as essential tools for visualising spatial variation in received signal strength, path loss, delay spread, and other key metrics [14]. These maps allow planners to identify coverage gaps, interference zones, and localised anomalies with far greater precision than classical models [14].

This thesis therefore emphasises the generation of high-fidelity radio maps using physics-based Ray Tracing techniques. Leveraging an open-source simulation framework, the study models realistic wireless propagation in complex urban settings. Special attention is given to UK cities, where dense architectural diversity, irregular street morphology, and challenging layouts provide highly relevant case studies for advanced propagation analysis.

## 1.2 Problem Statement and Research Gap in Urban Propagation Modeling

Reliable wireless connectivity has become indispensable for modern cities, yet conventional propagation models show clear limitations when applied to complex urban environments. Classical approaches such as the Okumura–Hata [9], FSPL [11], and COST-231 [10] models are largely empirical, relying on statistical averages and uniform assumptions about terrain and building distributions. While effective for broad coverage estimates, they fail to capture the irregular geometries and heterogeneous materials that define dense cityscapes.

Key shortcomings include the inability to incorporate critical geometric and material features — such as street orientation, building height variability, façade composition, rooftop structures, and canyon-like corridors — that strongly influence electromagnetic behaviour. For instance, glass façades can produce intense reflections, while narrow intersections generate diffraction and shadowing effects that cannot be represented through statistical approximations.

Moreover, these models typically operate at coarse spatial resolutions — tens to hundreds of metres [9] — which are insufficient for modern applications such as small-cell deployment, beamforming, vehicular communications, and advanced 5G/6G planning. These use cases demand fine-grained, location-specific predictions due to rapid spatial channel variations.

This gap between simplified empirical models and the high-resolution predictions required by next-generation systems highlights the need for deterministic simulation techniques that explicitly model electromagnetic interactions within realistic three-dimensional urban environments. Ray Tracing techniques have therefore gained increasing importance in wireless propagation research because they explicitly model the interaction of electromagnetic waves with realistic geometries and materials [2]. By incorporating accurate environmental representations, RT-based approaches provide significantly improved prediction fidelity and spatial resolution compared to conventional statistical models [2].

## 1.3 Ray Tracing as a Solution and the Role of RT

Ray Tracing (RT) offers a deterministic alternative to empirical models by simulating the physical behaviour of radio waves as they interact with surrounding objects and materials. Unlike statistical approaches, RT directly accounts for reflections, diffractions, scattering, penetration losses, and multipath propagation [2].

The deterministic nature of RT makes it particularly suitable for complex urban environments where signal behaviour is strongly influenced by local geometry and material properties. By modelling streets, trees and other vegetation, rooftops, and obstacles with high fidelity, RT enables precise estimation of spatial signal distributions and propagation characteristics [2]. This capability positions RT as a leading method for generating high-resolution radio environmental maps and supporting advanced wireless network planning [14].

This thesis employs NVIDIA's open-source Sionna RT, built on the Mitsuba 3 rendering engine [13] and the Dr.Jit compiler infrastructure [12]. Sionna RT provides differentiable Ray Tracing capabilities tailored for wireless research and digital twin applications [3], [4]. Its differentiable architecture allows calibration of scene parameters — such as materials, antenna configurations, and environmental features — against measured data, reducing prediction errors (RMSE, R²) through iterative refinement [3]. The framework remains highly suitable for detailed propagation analysis because of its flexibility, open-source nature, reproducibility, and integration with Python-based scientific workflows [3].

## 1.4 Study Area Selection and the Importance of Radio Environmental Maps

Urban regions in the United Kingdom were chosen as case studies due to their dense layouts, historical districts, irregular street geometries, and mixed architectural styles. These characteristics create highly complex propagation environments, making them ideal for investigating advanced electromagnetic behaviour using RT.

The selected areas include narrow streets, railways, variable building heights, residential and commercial zones, and diverse construction materials. This diversity enables analysis of how architectural and geometric features influence signal propagation, multipath richness, shadowing, and delay spread.

Radio environmental maps generated in these settings provide detailed spatial visualisations of signal behaviour. Unlike coarse statistical models, they reveal localised variations in coverage, interference, and attenuation [14]. Such insights are critical for modern wireless planning, where infrastructure deployment must balance technical performance with urban planning constraints.

This thesis emphasises detailed radio maps combined with path analysis using Sionna RT's path solver, enabling extraction of location-specific propagation insights and path loss measurements with high fidelity [3].

## 1.5 Research Questions and Objectives

To address the identified research challenges and bridge the gap between conventional propagation modelling and high-fidelity deterministic simulation, this thesis investigates the following research questions:

1. How accurately can Sionna RT generate high-resolution radio environmental maps within complex UK urban environments?
2. How do architectural features — such as narrow streets, dense building arrangements, and varied façades — affect signal propagation?
3. What spatial variations in signal strength, path loss, delay spread, and multipath richness can be observed across different urban regions?
4. How do RT-based predictions compare with classical models in accuracy, resolution, and applicability?

To answer these questions, the primary objectives of this thesis are:

- Develop realistic three-dimensional urban models using LiDAR, OpenStreetMap data, and geographic processing workflows suitable for Ray Tracing simulations.
- Prepare and optimise simulation scenes for compatibility with Sionna RT and differentiable propagation modelling.
- Conduct detailed electromagnetic propagation simulations using Sionna RT.
- Generate high-resolution radio environmental maps illustrating signal coverage, shadowing effects, and spatial propagation characteristics.
- Analyse path loss behaviour, multipath propagation, delay spread, and angular dispersion using path solver outputs.
- Evaluate the applicability, scalability, and limitations of open-source RT frameworks for wireless planning and digital twin applications.
- Investigate the impact of scene calibration, material tuning, and geometric refinement on reducing prediction errors such as RMSE and R².

## 1.6 Thesis Structure Overview

**[FIGURE 1 — PLACEHOLDER]**
*Research framework roadmap: Problem Definition (Ch.1) → Literature Gap (Ch.2) → Proposed Method (Ch.3) → Implementation (Ch.4) → Results & Validation (Ch.5) → Conclusions (Ch.6). To be inserted.*

Figure 1 illustrates the overall research framework, linking the problem definition, literature gap, proposed method, implementation, and validation stages that guide the development of this thesis. Each stage corresponds to a chapter, ensuring a logical progression from theoretical foundations to practical experimentation and final conclusions:

- **Chapter 1 – Research Problem** — Defines the engineering challenge, practical need, and scientific motivation underlying urban wireless propagation modeling.
- **Chapter 2 – Literature Gap** — Reviews existing propagation models, identifies missing knowledge, and highlights unresolved technical issues.
- **Chapter 3 – Proposed Method** — Presents the deterministic Ray Tracing approach, simulation framework, and scene generation methodology using EA LiDAR and OpenStreetMap data.
- **Chapter 4 – Implementation** — Details system modeling, simulation setup, data collection, and tool configuration within the Sionna RT environment.
- **Chapter 5 – Results & Validation** — Analyzes radio environmental maps, evaluates propagation metrics, and compares results with classical models.
- **Chapter 6 – Conclusions** — Summarizes findings, discusses limitations, and outlines future directions in differentiable Ray Tracing and digital twin applications.

This structure ensures methodological transparency, academic rigor, and practical relevance while establishing a comprehensive framework for advanced urban wireless propagation analysis.

---

*References for this chapter are numbered [1]–[14]; see `references.md` for the full, verified reference list shared across all chapters.*
