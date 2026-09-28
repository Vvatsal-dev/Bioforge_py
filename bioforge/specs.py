"""
specs.py - the equation cards shown on the Specifications page.

Each card is a dictionary. Formulas are written in LaTeX so Streamlit can
typeset them with st.latex(). Cards 01-06 come from the original website;
07-09 were added for the Lineweaver-Burk plot and the new Bioreactor module.
"""

CATEGORIES = {
    "all": "All Equations",
    "speed": "Core Speed (v)",
    "grip": "Molecular Grip (Km)",
    "turnover": "Turnover Rate (kcat)",
    "efficiency": "Catalytic Power",
    "environment": "Thermal & pH",
    "growth": "Microbial Growth",
}

EQUATIONS = [
    {
        "number": "01",
        "category": "speed",
        "badge": "Core Kinetics",
        "title": "Reaction Velocity (Michaelis-Menten Equation)",
        "formula": r"v = \frac{V_{max}\,[S]}{K_m + [S]}",
        "subtitle": "The gold-standard mathematical foundation describing enzymatic reaction rates.",
        "variables": [
            ("v", "Current catalytic velocity (reaction rate in µmol/s)"),
            ("V_{max}", "Maximum theoretical velocity under complete substrate saturation"),
            ("[S]", "Current substrate concentration in solution (mM)"),
            ("K_m", "Michaelis constant: substrate concentration at half-maximum velocity (½ Vmax)"),
        ],
        "plain": (
            "When substrate molecules are scarce, every added molecule speeds up the reaction directly. "
            "But when all enzyme pockets are occupied, adding more substrate changes nothing—the system "
            "hits a maximum speed ceiling (Vmax)."
        ),
        "example": (
            "Like cars at a toll plaza: if few cars arrive, processing increases linearly. At rush hour, "
            "all booths are full and traffic clears at a fixed maximum speed."
        ),
    },
    {
        "number": "02",
        "category": "grip",
        "badge": "Molecular Grip",
        "title": "Michaelis Constant (Km Affinity)",
        "formula": r"K_m = [S] \quad \text{when} \quad v = \tfrac{1}{2}V_{max}",
        "subtitle": "Measures how tightly an enzyme binds to its target substrate molecule.",
        "variables": [
            ("K_m", "Substrate density required to fill 50% of available active sites"),
            (r"\text{Low } K_m", "High affinity: tight grip, requires very little substrate to react"),
            (r"\text{High } K_m", "Low affinity: loose grip, requires dense substrate concentrations"),
        ],
        "plain": (
            "A lower Km means the enzyme has a \"magnetic\" sticky grasp—it can capture scarce nutrients "
            "efficiently even in dilute biological fluids."
        ),
        "example": (
            "Amylase has a low Km for starch (5.0 mM), allowing digestion to kick off the instant food "
            "touches saliva in your mouth."
        ),
    },
    {
        "number": "03",
        "category": "turnover",
        "badge": "Catalytic Turnover",
        "title": "Turnover Number (kcat)",
        "formula": r"k_{cat} = \frac{V_{max}}{[E]_{total}}",
        "subtitle": "Number of substrate molecules converted into product per active site per second.",
        "variables": [
            ("k_{cat}", "Turnover frequency (1/s, or catalytic constant)"),
            ("V_{max}", "Maximum rate achieved at full saturation"),
            ("[E]_{total}", "Total molar enzyme concentration present in solution"),
        ],
        "plain": (
            "Once a substrate molecule binds, how fast does the chemical magic happen before the enzyme "
            "lets go and grabs another? That turnover pace is kcat."
        ),
        "example": (
            "Catalase is a nature speed champion with kcat > 40,000,000 s⁻¹, converting toxic peroxides "
            "almost as fast as diffusion allows."
        ),
    },
    {
        "number": "04",
        "category": "efficiency",
        "badge": "Evolutionary Benchmark",
        "title": "Catalytic Perfection Score (kcat / Km)",
        "formula": r"\text{Efficiency} = \frac{k_{cat}}{K_m}",
        "subtitle": "The ultimate benchmark of an enzyme’s real-world catalytic performance.",
        "variables": [
            (r"k_{cat}/K_m", "Second-order rate constant (M⁻¹ · s⁻¹)"),
            (r"\text{Diffusion limit}", "10⁸ to 10⁹ M⁻¹ · s⁻¹ (the physical speed limit of liquid diffusion)"),
        ],
        "plain": (
            "Balances both grip and speed. An enzyme that binds tightly (low Km) and converts "
            "instantaneously (high kcat) approaches evolutionary \"catalytic perfection\"."
        ),
        "example": (
            "Enzymes like catalase and carbonic anhydrase operate at the physical diffusion "
            "barrier—limited only by how quickly molecules can physically collide."
        ),
    },
    {
        "number": "05",
        "category": "environment",
        "badge": "Thermodynamics",
        "title": "Thermal Peak & Arrhenius Inactivation",
        "formula": r"k = A\,e^{-E_a/(R\,T)} \quad (\text{active}) \qquad T > 55\,^{\circ}\mathrm{C} \Rightarrow \text{inactivated}",
        "subtitle": "How temperature boosts kinetic motion before fatally unraveling protein folds.",
        "variables": [
            ("E_a", "Activation energy required to trigger the chemical transition state"),
            ("T", "Absolute temperature in Kelvin (or °C + 273.15)"),
            ("R", "Universal Gas Constant (8.314 J / mol·K)"),
            (r"\text{Denaturation}", "Loss of tertiary structure above critical threshold (~55°C)"),
        ],
        "plain": (
            "Warming increases collision frequencies, doubling velocity every 10°C (Q10 rule). However, "
            "once temperature exceeds the enzyme’s thermal ceiling, thermal agitation breaks fragile "
            "hydrogen bonds and permanently denatures the active site."
        ),
        "example": "Boiling an egg: albumin proteins permanently unfold into an opaque white gel that can never re-fold.",
    },
    {
        "number": "06",
        "category": "environment",
        "badge": "Biochemical Charge",
        "title": "Acidity & Active-Site Ionization (pH Bell Curve)",
        "formula": r"[E]_{active} = \frac{[E]_{total}}{1 + \frac{[H^+]}{K_1} + \frac{K_2}{[H^+]}}",
        "subtitle": "The delicate proton balance required to preserve active site electric charge.",
        "variables": [
            ("[H^+]", "Hydronium ion concentration (pH = −log₁₀[H⁺])"),
            ("K_1,\\ K_2", "Acid-base ionization constants of key catalytic amino acid residues"),
            (r"\text{Optimum pH}", "The exact narrow window where both acid and base side-chains are functional"),
        ],
        "plain": (
            "Enzyme pockets rely on precise positive and negative charges to attract substrates. Acidic "
            "environments flood the pocket with protons, while basic fluids strip them away—both "
            "extinguishing catalytic power."
        ),
        "example": "Stomach pepsin thrives at acidic pH 1.5–2.0, whereas intestinal trypsin works at alkaline pH 8.0.",
    },
    {
        "number": "07",
        "category": "speed",
        "badge": "Linear Transform",
        "title": "Lineweaver-Burk Double-Reciprocal Plot",
        "formula": r"\frac{1}{v} = \frac{K_m}{V_{max}}\cdot\frac{1}{[S]} + \frac{1}{V_{max}}",
        "subtitle": "Turns the Michaelis-Menten curve into a straight line so Km and Vmax can be read off.",
        "variables": [
            (r"\text{slope}", "Km / Vmax"),
            (r"y\text{-intercept}", "1 / Vmax"),
            (r"x\text{-intercept}", "−1 / Km"),
        ],
        "plain": (
            "Curves are hard to read by eye, straight lines are easy. Taking the reciprocal of both axes "
            "straightens the curve, so one ruler gives you both kinetic constants."
        ),
        "example": "Used in every biochemistry lab to spot inhibitors: competitive inhibitors change the slope but not the y-intercept.",
    },
    {
        "number": "08",
        "category": "growth",
        "badge": "Bioreactor",
        "title": "Specific Growth Rate (μ) & Doubling Time",
        "formula": r"\mu = \frac{1}{X}\frac{dX}{dt} = \frac{d\,\ln X}{dt} \qquad t_d = \frac{\ln 2}{\mu}",
        "subtitle": "How fast each gram of cells makes more cells, the heartbeat of a fermentation.",
        "variables": [
            (r"\mu", "Specific growth rate (h⁻¹)"),
            ("X", "Biomass concentration (g/L), measured as optical density OD600"),
            ("t_d", "Doubling time: how long the population takes to double"),
        ],
        "plain": (
            "The absolute growth rate dX/dt keeps rising as the culture gets denser, but μ tells you how "
            "fast each cell divides. μ is highest in the exponential phase and falls to zero when food runs out."
        ),
        "example": "E. coli in glucose minimal medium at 37 °C reaches μ ≈ 0.6–0.7 h⁻¹, a doubling roughly every hour.",
    },
    {
        "number": "09",
        "category": "growth",
        "badge": "Bioreactor",
        "title": "Monod Growth Kinetics",
        "formula": r"\mu = \mu_{max}\,\frac{S}{K_s + S}",
        "subtitle": "The Michaelis-Menten equation's microbial cousin: growth rate depends on food supply.",
        "variables": [
            (r"\mu_{max}", "Maximum specific growth rate when nutrients are plentiful (h⁻¹)"),
            ("S", "Limiting substrate concentration, e.g. glucose (g/L)"),
            ("K_s", "Half-saturation constant: glucose level giving ½ μmax"),
        ],
        "plain": (
            "Same shape as the enzyme curve: plenty of glucose means full-speed growth, and as glucose "
            "disappears growth stalls, which is why the batch culture enters stationary phase."
        ),
        "example": "In the Bioreactor tab, growth stops at the exact moment glucose hits zero, and the dissolved oxygen spikes back up.",
    },
]
