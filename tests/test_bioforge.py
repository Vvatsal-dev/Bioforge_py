"""
Quick checks that the maths behaves like real biochemistry.
Run from the project folder with:   python -m pytest -q
"""

import io
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bioforge import bioreactor as br  # noqa: E402
from bioforge import catalog, kinetics  # noqa: E402


# ------------------------------------------------------------- catalogue
def test_catalog_has_five_enzymes_with_new_pairs():
    cat = catalog.get_default_catalog()
    assert list(cat) == ["lactase", "amylase", "catalase", "urease", "invertase"]
    assert (cat["urease"]["km"], cat["urease"]["vmax"], cat["urease"]["optimal_temp"], cat["urease"]["optimal_ph"]) == (10.5, 22.0, 37, 7.0)
    assert (cat["invertase"]["km"], cat["invertase"]["vmax"], cat["invertase"]["optimal_temp"], cat["invertase"]["optimal_ph"]) == (26.0, 14.5, 50, 4.5)


def test_custom_enzyme_ids_are_unique():
    existing = {"syn-hydrolase-beta"}
    enzyme = catalog.create_custom_enzyme("Syn-Hydrolase Beta", "Cellulose", "Cellobiose", 7.5, 12, 45, 6.0, existing)
    assert enzyme["id"] == "syn-hydrolase-beta-1"
    assert enzyme["is_custom"]


# -------------------------------------------------------------- kinetics
def test_michaelis_menten_half_vmax_at_km():
    assert kinetics.michaelis_menten(12.0, 8.5, 12.0) == pytest.approx(8.5 / 2)


def test_lineweaver_burk_is_a_straight_line():
    s = np.array([2.0, 5.0, 10.0, 40.0])
    x, y = kinetics.lineweaver_burk(s, vmax=10.0, km=5.0)
    slope, intercept = np.polyfit(x, y, 1)
    assert slope == pytest.approx(5.0 / 10.0)
    assert intercept == pytest.approx(1 / 10.0)


def test_temperature_denaturation_collapses_activity():
    assert kinetics.temperature_factor(37, 37) == 1.0
    assert kinetics.temperature_factor(72, 37) < 0.01 + 1e-9
    assert kinetics.is_denatured(56) and not kinetics.is_denatured(55)


def test_optimal_run_reaches_high_yield_and_denatured_run_does_not():
    lactase = catalog.ENZYME_CATALOG["lactase"]
    good = kinetics.simulate_reaction(lactase, 37, 6.5, 2, 25)
    hot = kinetics.simulate_reaction(lactase, 72, 6.5, 2, 25)
    assert good["progress_pct"].iloc[-1] > 90
    assert hot["progress_pct"].iloc[-1] < 5
    assert good["time_s"].iloc[-1] == pytest.approx(20.0)


# ------------------------------------------------------------ bioreactor
@pytest.fixture(scope="module")
def batch():
    return br.load_builtin_dataset()


def test_dataset_has_required_columns(batch):
    assert list(batch.columns[:5]) == br.ALL_COLUMNS
    assert batch[br.TIME].min() == 0 and batch[br.TIME].max() == 24


def test_post_cutoff_average_matches_manual_filter(batch):
    after, overall, n = br.post_cutoff_average(batch, br.DO, 10.0)
    manual = batch.loc[batch[br.TIME] >= 10.0, br.DO]
    assert after == pytest.approx(manual.mean())
    assert overall == pytest.approx(batch[br.DO].mean())
    assert n == len(manual)


def test_peak_growth_is_the_maximum_of_dod_dt(batch):
    peak = br.find_peak_growth(batch)
    rates = np.gradient(batch[br.OD], batch[br.TIME])
    assert peak["time"] == batch[br.TIME].iloc[int(np.argmax(rates))]


def test_mu_max_is_realistic_for_e_coli(batch):
    mu = br.find_mu_max(batch)["mu"]
    assert 0.5 < mu < 0.8          # E. coli on glucose minimal medium
    assert 0.4 < br.biomass_yield(batch) < 0.55


def test_phases_are_in_biological_order(batch):
    names = [p["Phase"] for p in br.detect_phases(batch)]
    assert names == ["Lag", "Exponential", "Stationary", "Decline"]


def test_uploaded_csv_without_mu_column_is_accepted():
    csv = "time_hours,cell_density_OD600,dissolved_oxygen_pct,glucose_conc_gL\n0,0.1,100,5\n1,0.2,90,4.5\n2,0.4,70,3.5\n"
    df, notes = br.parse_uploaded_csv(io.StringIO(csv))
    assert br.MU in df.columns
    assert df[br.MU].iloc[1] == pytest.approx(math.log(0.4 / 0.1) / 2, rel=1e-3)


def test_uploaded_csv_missing_columns_is_rejected():
    with pytest.raises(br.DatasetError):
        br.parse_uploaded_csv(io.StringIO("time_hours,cell_density_OD600\n0,1\n1,2\n2,3\n"))
