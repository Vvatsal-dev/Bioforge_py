"""
catalog.py - the BioForge enzyme library.

Every enzyme is a plain Python dictionary, and the whole catalogue is a
dictionary of those dictionaries (key = enzyme id). This keeps the data easy
to read, print, loop over and extend - no classes needed.

Units used everywhere in BioForge:
    km            -> mM        (Michaelis constant)
    vmax          -> umol/s    (maximum velocity)
    optimal_temp  -> degrees C
    optimal_ph    -> pH units
"""

import copy
import re

# ---------------------------------------------------------------------------
# The 5 standard benchmark biocatalysts
# (the first three are unchanged from the original BioForge website,
#  Urease and Invertase were added after the academic review)
# ---------------------------------------------------------------------------
ENZYME_CATALOG = {
    "lactase": {
        "id": "lactase",
        "name": "Lactase",
        "substrate": "Lactose",
        "product": "Glucose + Galactose",
        "equation": "Lactose → Glucose + Galactose",
        "ec_number": "EC 3.2.1.108",
        "km": 12.0,
        "vmax": 8.5,
        "optimal_temp": 37,
        "optimal_ph": 6.5,
        "reaction_type": "Disaccharide Cleavage",
        "mechanism": (
            "Hydrolyzes β-D-galactoside linkage of lactose into monomeric "
            "glucose and galactose sugars."
        ),
        "beginner_tip": (
            "Individuals with lactose intolerance lack sufficient amounts of "
            "this brush-border enzyme."
        ),
        "subtitle": "Splits milk sugar lactose into easily digestible glucose and galactose",
        "is_custom": False,
    },
    "amylase": {
        "id": "amylase",
        "name": "Amylase",
        "substrate": "Starch",
        "product": "Glucose",
        "equation": "Starch Breakdown",
        "ec_number": "EC 3.2.1.1",
        "km": 5.0,
        "vmax": 10.0,
        "optimal_temp": 37,
        "optimal_ph": 6.7,
        "reaction_type": "Hydrolysis (Glycosidic)",
        "mechanism": (
            "Cleaves internal α-1,4-glycosidic bonds within starch "
            "polysaccharides, producing maltose and glucose without ATP."
        ),
        "beginner_tip": (
            "Found in saliva and pancreas! It begins the digestive breakdown of "
            "bread and rice almost instantly."
        ),
        "subtitle": "Breaks complex starch polymers down into sweet maltose and glucose sugars",
        "is_custom": False,
    },
    "catalase": {
        "id": "catalase",
        "name": "Catalase",
        "substrate": "Hydrogen Peroxide",
        "product": "Water + Oxygen",
        "equation": "2 H₂O₂ → 2 H₂O + O₂",
        "ec_number": "EC 1.11.1.6",
        "km": 25.0,
        "vmax": 15.0,
        "optimal_temp": 37,
        "optimal_ph": 7.0,
        "reaction_type": "Oxidoreductase Decomposition",
        "mechanism": (
            "Contains four heme groups that convert toxic intracellular H₂O₂ "
            "into water and effervescent oxygen gas."
        ),
        "beginner_tip": (
            "Catalase has one of the highest turnover rates in nature—converting "
            "millions of H₂O₂ molecules every second."
        ),
        "subtitle": "Rapidly neutralizes hydrogen peroxide into harmless water and oxygen gas bubbles",
        "is_custom": False,
    },
    # ---------------- NEW (academic review) ----------------
    "urease": {
        "id": "urease",
        "name": "Urease",
        "substrate": "Urea",
        "product": "Ammonia (NH₃) + Carbon Dioxide (CO₂)",
        "equation": "CO(NH₂)₂ + H₂O → 2 NH₃ + CO₂",
        "ec_number": "EC 3.5.1.5",
        "km": 10.5,
        "vmax": 22.0,
        "optimal_temp": 37,
        "optimal_ph": 7.0,
        "reaction_type": "Amide Hydrolysis / Amidohydrolase",
        "mechanism": (
            "Rapidly hydrolyzes urea into carbonic acid and ammonia using a "
            "nickel-containing (bi-nickel) active site; widely studied in "
            "environmental and agricultural biotechnology."
        ),
        "beginner_tip": (
            "Urease was the first enzyme ever crystallized (J. B. Sumner, 1926), "
            "the experiment that proved enzymes are proteins."
        ),
        "subtitle": "Breaks urea down into ammonia and carbon dioxide (soil and fertilizer chemistry)",
        "is_custom": False,
    },
    "invertase": {
        "id": "invertase",
        "name": "Invertase (Sucrase)",
        "substrate": "Sucrose",
        "product": "Glucose + Fructose (Invert Sugar)",
        "equation": "Sucrose + H₂O → Glucose + Fructose",
        "ec_number": "EC 3.2.1.26",
        "km": 26.0,
        "vmax": 14.5,
        "optimal_temp": 50,
        "optimal_ph": 4.5,
        "reaction_type": "Glycosidic Hydrolysis",
        "mechanism": (
            "Industrial workhorse enzyme (β-fructofuranosidase) that hydrolyzes "
            "terminal non-reducing β-D-fructofuranoside residues in sucrose."
        ),
        "beginner_tip": (
            "Confectioners add invertase to make the liquid centres of "
            "chocolate-covered cherries: it slowly turns solid sucrose fondant into "
            "runny invert-sugar syrup."
        ),
        "subtitle": "Splits table sugar (sucrose) into a sweeter glucose + fructose syrup",
        "is_custom": False,
    },
}

# The order enzymes are shown in drop-downs and cards
BUILT_IN_IDS = list(ENZYME_CATALOG.keys())


def get_default_catalog():
    """Return a fresh, independent copy of the catalogue (safe to modify)."""
    return copy.deepcopy(ENZYME_CATALOG)


def make_enzyme_id(name, existing_ids):
    """Turn a name like 'Syn-Hydrolase Beta' into a unique id 'syn-hydrolase-beta'.

    If the id already exists, a counter is added: 'syn-hydrolase-beta-1', ...
    """
    raw_id = re.sub(r"[^a-z0-9]", "-", name.lower()) or "custom-enzyme"
    new_id = raw_id
    counter = 1
    while new_id in existing_ids:
        new_id = f"{raw_id}-{counter}"
        counter += 1
    return new_id


def create_custom_enzyme(name, substrate, product, km, vmax, optimal_temp, optimal_ph, existing_ids):
    """Build a custom enzyme dictionary (same fields as the built-in ones)."""
    name = name.strip() or "Custom Enzyme"
    substrate = substrate.strip() or "Substrate"
    product = product.strip() or "Product"
    enzyme_id = make_enzyme_id(name, existing_ids)

    return {
        "id": enzyme_id,
        "name": name,
        "substrate": substrate,
        "product": product,
        "equation": f"{substrate} → {product}",
        "ec_number": "Engineered construct",
        "km": float(km),
        "vmax": float(vmax),
        "optimal_temp": int(optimal_temp),
        "optimal_ph": float(optimal_ph),
        "reaction_type": "Engineered Synthetic Biocatalysis",
        "mechanism": (
            f"Synthetically tailored active site configured with Km = {km:.1f} mM "
            f"and Vmax = {vmax:.1f} µmol/s."
        ),
        "beginner_tip": "Constructed inside the BioForge Enzyme Studio workbench.",
        "subtitle": f"Engineered biocatalyst converting {substrate} to {product}",
        "is_custom": True,
    }


def enzyme_label(enzyme):
    """Text used in the enzyme drop-down, e.g. 'Lactase + Lactose'."""
    label = f"{enzyme['name']} + {enzyme['substrate']}"
    if enzyme.get("is_custom"):
        label += "  ★ (Custom)"
    return label
