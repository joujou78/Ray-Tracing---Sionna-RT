# Chapter 1 - Introduction

This chapter introduces the research problem addressed by this thesis. It presents the urban wireless propagation context, states the problem and research gap, introduces Ray Tracing as the proposed solution, describes the selected study areas, and sets out the research questions and objectives that guide the remainder of the work.

## 1.1 Wireless Communication in the Urban Context

Mobile data demand continues to grow, with 5G network deployment as the primary infrastructure response [1]. Reliable coverage prediction is a prerequisite for that deployment, and urban propagation is difficult to predict accurately: dense, irregular building geometries composed of stone, brick, glass, vegetation, and concrete introduce reflection, diffraction, scattering, penetration losses, and shadowing, producing severe multipath propagation and rapid spatial signal fluctuations [2]. Traditional models, including Okumura-Hata [9], Free-Space Path Loss (FSPL) [11], and COST-231 [10], rely on empirical assumptions and coarse spatial resolution, and are consequently unsuitable for the high-precision urban planning this thesis addresses (Section 1.2).

Deterministic, geometry-aware approaches such as Ray Tracing (RT) address this limitation by explicitly modelling electromagnetic interactions with realistic geometries and materials, enabling the generation of high-resolution radio environmental maps that reveal localised coverage gaps, interference zones, and anomalies with far greater precision than classical models [2], [14].

This thesis emphasises the generation of such high-fidelity radio maps using physics-based Ray Tracing, applied to real UK sites. Their dense architectural diversity, irregular street morphology, and mixed construction materials provide directly relevant case studies for the propagation-modelling challenge described above.

## 1.2 Problem Statement and Research Gap in Urban Propagation Modeling

Classical propagation models, including Okumura-Hata [9], FSPL [11], and COST-231 [10], are largely empirical, relying on statistical averages and uniform assumptions about terrain and building distributions. Their central shortcoming is an inability to incorporate the geometric and material features, such as street orientation, building height variability, and facade composition, that strongly influence electromagnetic behaviour: glass facades produce intense reflections, and narrow intersections generate diffraction and shadowing, neither of which a statistical approximation can represent. These models also typically operate at coarse spatial resolutions of tens to hundreds of metres [9], insufficient for applications such as small-cell deployment and beamforming, which require fine-grained, location-specific predictions.

This gap between simplified empirical models and the resolution such applications require motivates the deterministic simulation approach adopted in this thesis: explicitly modelling electromagnetic interactions within a realistic three-dimensional representation of each site, rather than relying on statistical averages [2].

## 1.3 Ray Tracing as a Solution and the Role of RT

Ray Tracing (RT) offers a deterministic alternative to empirical models, directly simulating how radio waves reflect, diffract, scatter, and penetrate as they interact with the geometry and materials of a real environment [2]. By modelling streets, vegetation, rooftops, and obstacles with high fidelity, RT enables precise estimation of spatial signal distributions, positioning it as a leading method for generating the high-resolution radio environmental maps this thesis relies on [14].

This thesis uses NVIDIA's open-source Sionna RT, built on the Mitsuba 3 rendering engine [13] and the Dr.Jit differentiable compiler [12], which provides differentiable Ray Tracing capabilities [3]. Its differentiable architecture allows scene parameters, principally material properties, to be calibrated against measured data, reducing prediction error (RMSE, R²) through iterative refinement [3]. All simulations in this thesis are executed in GPU mode on hardware provided by the university (Section 4.2).

## 1.4 Study Area Selection and the Importance of Radio Environmental Maps

Urban regions in the United Kingdom were chosen as case studies due to their dense layouts, historical districts, irregular street geometries, and mixed architectural styles. These characteristics create highly complex propagation environments, making them ideal for investigating advanced electromagnetic behaviour using RT.

The selected areas include narrow streets, railways, variable building heights, residential and commercial zones, and diverse construction materials. This diversity enables analysis of how architectural and geometric features influence signal propagation, multipath richness, shadowing, and delay spread.

Radio environmental maps generated in these settings provide detailed spatial visualisations of signal behaviour. Unlike coarse statistical models, they reveal localised variations in coverage, interference, and attenuation [14]. Such insights are critical for modern wireless planning, where infrastructure deployment must balance technical performance with urban planning constraints.

This thesis emphasises detailed radio maps combined with path analysis using Sionna RT's path solver, enabling extraction of location-specific propagation insights and path loss measurements with high fidelity [3].

## 1.5 Research Questions and Objectives

To address the identified research challenges and bridge the gap between conventional propagation modelling and high-fidelity deterministic simulation, this thesis investigates the following research questions:

1. How accurately can Sionna RT generate high-resolution radio environmental maps within complex UK urban environments?
2. How do architectural features, such as narrow streets, dense building arrangements, and varied facades, affect signal propagation?
3. What spatial variations in signal strength, path loss, delay spread, and multipath richness can be observed across different urban regions?
4. How do RT-based predictions compare with classical models in accuracy, resolution, and applicability?

To answer these questions, the primary objectives of this thesis are:

- Develop realistic three-dimensional urban models using LiDAR, OpenStreetMap data, and geographic processing workflows suitable for Ray Tracing simulations.
- Prepare and optimise simulation scenes for compatibility with Sionna RT and differentiable propagation modelling.
- Conduct detailed electromagnetic propagation simulations using Sionna RT.
- Generate high-resolution radio environmental maps illustrating signal coverage, shadowing effects, and spatial propagation characteristics.
- Analyse path loss behaviour, multipath propagation, delay spread, and angular dispersion using path solver outputs.
- Evaluate the applicability, scalability, and limitations of open-source RT frameworks for wireless planning.
- Investigate the impact of scene calibration, material tuning, and geometric refinement on reducing prediction errors such as RMSE and R².

## 1.6 Thesis Structure Overview

**[FIGURE 1 - PLACEHOLDER]**
*Research framework roadmap: Problem Definition (Ch.1) → Literature Gap (Ch.2) → Proposed Method (Ch.3) → Implementation (Ch.4) → Results & Validation (Ch.5) → Discussion and Impact (Ch.6) → Conclusion and Future Work (Ch.7). To be inserted.*

Figure 1 illustrates the overall research framework, linking the problem definition, literature gap, proposed method, implementation, and validation stages that guide the development of this thesis. Each stage corresponds to a chapter, ensuring a logical progression from theoretical foundations to practical experimentation and final conclusions:

- **Chapter 1 - Research Problem** - Defines the engineering challenge, practical need, and scientific motivation underlying urban wireless propagation modeling.
- **Chapter 2 - Literature Gap** - Reviews existing propagation models, identifies missing knowledge, and highlights unresolved technical issues.
- **Chapter 3 - Proposed Method** - Presents the deterministic Ray Tracing approach, simulation framework, and scene generation methodology using EA LiDAR and OpenStreetMap data.
- **Chapter 4 - Implementation** - Details system modeling, simulation setup, data collection, and tool configuration within the Sionna RT environment.
- **Chapter 5 - Results & Validation** - Analyzes radio environmental maps, evaluates propagation metrics, and compares results with classical models.
- **Chapter 6 - Discussion and Impact** - Interprets the scientific and engineering significance of the results validated in Chapter 5, and the limited environmental, economic, and societal implications this project's own data can support.
- **Chapter 7 - Conclusion and Future Work** - Summarises the research findings, states plainly which research questions and objectives were fully, partially, or not met, and proposes concrete next steps.

---

*References for this chapter are [1]-[3] and [9]-[14]; see `references.md` for the full, verified reference list shared across all chapters.*
