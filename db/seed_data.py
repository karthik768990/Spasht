"""
Seed script — populates departments/vendors/tenders/bids in NeonDB (Postgres)
with a synthetic dataset sized to actually validate HHI (last test run showed
too-small samples make HHI meaningless — this script deliberately generates
enough tenders per group to avoid that).

USAGE
-----
    export DATABASE_URL="postgresql+psycopg2://user:pass@host/dbname"
    python seed_data.py

GROUND TRUTH (documented so you can check the scoring engine's output
against known answers, not just "does it run"):

  - "General Admin / IT Hardware"        -> COMPETITIVE: 6 vendors rotating
                                             wins roughly evenly across 80 tenders.
                                             Expect LOW HHI.
  - "PWD Zone 4 / Road Construction"     -> RIGGED: 1 vendor wins ~85% of 80
                                             tenders. Expect HIGH HHI, plus
                                             narrow eligibility text overlap
                                             on a chunk of them.
  - "Health Dept / Medical Supplies"     -> MIXED: 3 vendors, ~50/30/20 split
                                             across 60 tenders, with ~12
                                             single-bidder tenders sprinkled in.
                                             Expect MODERATE HHI.
  - "Water Board / Pipeline Maintenance" -> COMPETITIVE: 5 vendors, near-even
                                             split across 60 tenders. Expect LOW HHI.
                                             (a second "normal" baseline group,
                                             so you're not just comparing 1 clean
                                             group vs 1 dirty group)
  - "Education Dept / School Furniture"  -> MODERATELY RIGGED: 2 vendors splitting
                                             ~65/35 across 50 tenders. Expect
                                             MODERATE-HIGH HHI — a deliberate
                                             "gray zone" case to test whether your
                                             thresholds distinguish this from the
                                             fully-rigged PWD group.

Scale is controlled by the *_COUNT constants below — bump them further if
you want an even larger stress-test dataset; the group logic is written to
scale independent of count.

Re-run this script anytime to wipe and regenerate (it truncates existing
rows first) — useful for iterating on your scoring thresholds against a
fresh, known dataset.
"""

import os
import random
import sys
from datetime import date, timedelta

from sqlalchemy import create_engine, text

random.seed(42)  # reproducible runs — important so you can compare tuning changes


def get_engine():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("[error] DATABASE_URL not set. Export it first, e.g.:")
        print('  export DATABASE_URL="postgresql+psycopg2://user:pass@host/dbname"')
        sys.exit(1)
    return create_engine(database_url)


def truncate_all(conn):
    # Order matters due to FK constraints; CASCADE handles anomaly_scores too.
    conn.execute(text("TRUNCATE anomaly_scores, bids, tenders, vendors, departments RESTART IDENTITY CASCADE;"))


def random_date(start_year=2023, end_year=2025):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# Tender counts per group — bump these for an even larger stress test.
IT_HARDWARE_COUNT = 80
ROAD_CONSTRUCTION_COUNT = 80
MEDICAL_SUPPLIES_COUNT = 60
PIPELINE_MAINTENANCE_COUNT = 60
SCHOOL_FURNITURE_COUNT = 50


def seed(conn):
    # --- Departments ---
    dept_ids = {}
    for name, region in [
        ("General Admin", "Zone A"),
        ("PWD Zone 4", "Zone D"),
        ("Health Dept", "Zone C"),
        ("Water Board", "Zone B"),
        ("Education Dept", "Zone E"),
    ]:
        result = conn.execute(
            text("INSERT INTO departments (name, region) VALUES (:n, :r) RETURNING department_id"),
            {"n": name, "r": region},
        )
        dept_ids[name] = result.scalar()

    # --- Vendors ---
    vendor_names = [
        "Alpha Systems Pvt Ltd", "Beta Computech", "Gamma IT Solutions",
        "Delta Technologies", "Epsilon Hardware Co", "Zeta Peripherals",
        "Suvidha Constructions Pvt Ltd", "Nirman Infra Works", "Pathway Builders",
        "MedSure Distributors", "CarePlus Pharma Supply", "Wellness Traders",
        "AquaFlow Engineering", "Rainline Contractors", "Bluewater Pipeworks",
        "ClearFlow Systems", "Riverbend Utilities",
        "Vidya Furnishings", "Study Interiors Pvt Ltd",
    ]
    vendor_ids = {}
    for name in vendor_names:
        result = conn.execute(
            text("INSERT INTO vendors (name, registered_address, registration_date) "
                 "VALUES (:n, :a, :d) RETURNING vendor_id"),
            {"n": name, "a": f"{random.randint(1,999)} Industrial Area", "d": random_date(2015, 2020)},
        )
        vendor_ids[name] = result.scalar()

    # --- Group 1: General Admin / IT Hardware — COMPETITIVE (low HHI expected) ---
    it_vendors = ["Alpha Systems Pvt Ltd", "Beta Computech", "Gamma IT Solutions",
                  "Delta Technologies", "Epsilon Hardware Co", "Zeta Peripherals"]
    it_eligibility_variants = [
        "Bidder must have {n} years experience supplying desktop computers and printers to government offices.",
        "Vendor should possess prior experience of at least {n} years in computer hardware supply for public sector.",
        "Applicant must demonstrate {n}+ years supplying IT peripherals to any state or central government body.",
    ]

    for i in range(IT_HARDWARE_COUNT):
        winner = it_vendors[i % len(it_vendors)]  # rotates roughly evenly
        text_variant = it_eligibility_variants[i % len(it_eligibility_variants)]
        elig_text = text_variant.format(n=random.choice([2, 3, 4]))
        estimated = random.randint(400000, 600000)

        tid = conn.execute(
            text("INSERT INTO tenders (department_id, category, region, eligibility_text, "
                 "estimated_value, award_value, published_date, award_date, status) "
                 "VALUES (:dept, 'IT Hardware', 'Zone A', :elig, :est, :award, :pub, :awd, 'awarded') "
                 "RETURNING tender_id"),
            {"dept": dept_ids["General Admin"], "elig": elig_text, "est": estimated,
             "award": estimated * random.uniform(0.92, 0.99),
             "pub": random_date(), "awd": random_date()},
        ).scalar()

        # 2-3 bidders per tender, winner as defined above
        bidders = random.sample([v for v in it_vendors if v != winner], k=random.choice([1, 2]))
        bidders.append(winner)
        for v in bidders:
            conn.execute(
                text("INSERT INTO bids (tender_id, vendor_id, bid_amount, is_winner) "
                     "VALUES (:t, :v, :amt, :win)"),
                {"t": tid, "v": vendor_ids[v], "amt": estimated * random.uniform(0.9, 1.05),
                 "win": (v == winner)},
            )

    # --- Group 2: PWD Zone 4 / Road Construction — RIGGED (high HHI expected) ---
    road_vendors = ["Suvidha Constructions Pvt Ltd", "Nirman Infra Works", "Pathway Builders"]
    dominant_vendor = "Suvidha Constructions Pvt Ltd"

    narrow_eligibility_variants = [
        "Contractor must hold Class-A road construction license and have completed at least 5 km of rural road work.",
        "Contractor must hold Class-A road construction license, have completed at least 5 km of rural road work, "
        "and must own a proprietary asphalt-mixing unit model AX-500.",  # the "narrowed for one vendor" version
    ]

    for i in range(ROAD_CONSTRUCTION_COUNT):
        # Dominant vendor wins ~85% of the time — deliberate planted anomaly
        winner = dominant_vendor if random.random() < 0.85 else random.choice(
            [v for v in road_vendors if v != dominant_vendor]
        )
        # Narrow/suspicious eligibility text on ~1/3 of tenders (correlated with dominant vendor winning)
        elig_text = narrow_eligibility_variants[1] if (winner == dominant_vendor and random.random() < 0.4) \
            else narrow_eligibility_variants[0]
        estimated = random.randint(8000000, 9500000)

        tid = conn.execute(
            text("INSERT INTO tenders (department_id, category, region, eligibility_text, "
                 "estimated_value, award_value, published_date, award_date, status) "
                 "VALUES (:dept, 'Road Construction', 'Zone D', :elig, :est, :award, :pub, :awd, 'awarded') "
                 "RETURNING tender_id"),
            {"dept": dept_ids["PWD Zone 4"], "elig": elig_text, "est": estimated,
             "award": estimated * random.uniform(0.95, 0.99),
             "pub": random_date(), "awd": random_date()},
        ).scalar()

        # Often only 1-2 bidders (low turnout is itself part of the planted pattern)
        num_bidders = random.choice([1, 1, 2])
        bidders = [winner]
        if num_bidders == 2:
            bidders.append(random.choice([v for v in road_vendors if v != winner]))
        for v in bidders:
            conn.execute(
                text("INSERT INTO bids (tender_id, vendor_id, bid_amount, is_winner) "
                     "VALUES (:t, :v, :amt, :win)"),
                {"t": tid, "v": vendor_ids[v], "amt": estimated * random.uniform(0.95, 1.05),
                 "win": (v == winner)},
            )

    # --- Group 3: Health Dept / Medical Supplies — MIXED (moderate HHI expected) ---
    health_vendors = ["MedSure Distributors", "CarePlus Pharma Supply", "Wellness Traders"]
    health_weights = [0.5, 0.3, 0.2]

    single_bidder_indices = set(range(3, MEDICAL_SUPPLIES_COUNT, 5))  # every 5th tender starting at 3 (~12 total)

    for i in range(MEDICAL_SUPPLIES_COUNT):
        estimated = random.randint(250000, 400000)
        elig_text = "Vendor must be a licensed pharmaceutical distributor registered with the state drug controller."

        tid = conn.execute(
            text("INSERT INTO tenders (department_id, category, region, eligibility_text, "
                 "estimated_value, award_value, published_date, award_date, status) "
                 "VALUES (:dept, 'Medical Supplies', 'Zone C', :elig, :est, :award, :pub, :awd, 'awarded') "
                 "RETURNING tender_id"),
            {"dept": dept_ids["Health Dept"], "elig": elig_text, "est": estimated,
             "award": estimated * random.uniform(0.95, 0.99),
             "pub": random_date(), "awd": random_date()},
        ).scalar()

        winner = random.choices(health_vendors, weights=health_weights, k=1)[0]
        # Sprinkle in single-bidder tenders deliberately (~12 across the group)
        if i in single_bidder_indices:
            bidders = [winner]
        else:
            bidders = random.sample([v for v in health_vendors if v != winner], k=1)
            bidders.append(winner)

        for v in bidders:
            conn.execute(
                text("INSERT INTO bids (tender_id, vendor_id, bid_amount, is_winner) "
                     "VALUES (:t, :v, :amt, :win)"),
                {"t": tid, "v": vendor_ids[v], "amt": estimated * random.uniform(0.9, 1.05),
                 "win": (v == winner)},
            )

    # --- Group 4: Water Board / Pipeline Maintenance — COMPETITIVE (second clean baseline) ---
    water_vendors = ["AquaFlow Engineering", "Rainline Contractors", "Bluewater Pipeworks",
                      "ClearFlow Systems", "Riverbend Utilities"]
    water_eligibility_variants = [
        "Bidder must have {n} years experience in municipal water pipeline installation or maintenance.",
        "Vendor should demonstrate at least {n} years handling public water infrastructure contracts.",
        "Applicant must show {n}+ years of experience in water distribution network upkeep for government bodies.",
    ]

    for i in range(PIPELINE_MAINTENANCE_COUNT):
        winner = water_vendors[i % len(water_vendors)]  # even rotation, like IT Hardware
        text_variant = water_eligibility_variants[i % len(water_eligibility_variants)]
        elig_text = text_variant.format(n=random.choice([2, 3, 4]))
        estimated = random.randint(600000, 1200000)

        tid = conn.execute(
            text("INSERT INTO tenders (department_id, category, region, eligibility_text, "
                 "estimated_value, award_value, published_date, award_date, status) "
                 "VALUES (:dept, 'Pipeline Maintenance', 'Zone B', :elig, :est, :award, :pub, :awd, 'awarded') "
                 "RETURNING tender_id"),
            {"dept": dept_ids["Water Board"], "elig": elig_text, "est": estimated,
             "award": estimated * random.uniform(0.92, 0.99),
             "pub": random_date(), "awd": random_date()},
        ).scalar()

        bidders = random.sample([v for v in water_vendors if v != winner], k=random.choice([1, 2]))
        bidders.append(winner)
        for v in bidders:
            conn.execute(
                text("INSERT INTO bids (tender_id, vendor_id, bid_amount, is_winner) "
                     "VALUES (:t, :v, :amt, :win)"),
                {"t": tid, "v": vendor_ids[v], "amt": estimated * random.uniform(0.9, 1.05),
                 "win": (v == winner)},
            )

    # --- Group 5: Education Dept / School Furniture — MODERATELY RIGGED (gray-zone test) ---
    furniture_vendors = ["Vidya Furnishings", "Study Interiors Pvt Ltd"]
    dominant_furniture_vendor = "Vidya Furnishings"
    furniture_eligibility = ("Bidder must supply ISI-certified school furniture and have prior "
                              "experience with government educational institution contracts.")

    for i in range(SCHOOL_FURNITURE_COUNT):
        # ~65/35 split — deliberately less extreme than the 85% PWD rigging,
        # to test whether your thresholds tell "moderate skew" apart from
        # "fully rigged" rather than lumping both into one bucket.
        winner = dominant_furniture_vendor if random.random() < 0.65 else \
            [v for v in furniture_vendors if v != dominant_furniture_vendor][0]
        estimated = random.randint(150000, 300000)

        tid = conn.execute(
            text("INSERT INTO tenders (department_id, category, region, eligibility_text, "
                 "estimated_value, award_value, published_date, award_date, status) "
                 "VALUES (:dept, 'School Furniture', 'Zone E', :elig, :est, :award, :pub, :awd, 'awarded') "
                 "RETURNING tender_id"),
            {"dept": dept_ids["Education Dept"], "elig": furniture_eligibility, "est": estimated,
             "award": estimated * random.uniform(0.93, 0.99),
             "pub": random_date(), "awd": random_date()},
        ).scalar()

        bidders = [winner]
        if random.random() < 0.7:  # most tenders still have 2 bidders, some don't
            bidders.append([v for v in furniture_vendors if v != winner][0])
        for v in bidders:
            conn.execute(
                text("INSERT INTO bids (tender_id, vendor_id, bid_amount, is_winner) "
                     "VALUES (:t, :v, :amt, :win)"),
                {"t": tid, "v": vendor_ids[v], "amt": estimated * random.uniform(0.9, 1.05),
                 "win": (v == winner)},
            )

    print("[info] Seed complete.")
    print("[info] Ground truth to check your scoring engine against:")
    print(f"  - General Admin / IT Hardware        -> {IT_HARDWARE_COUNT} tenders, expect LOW HHI (6 vendors rotating)")
    print(f"  - PWD Zone 4 / Road Construction      -> {ROAD_CONSTRUCTION_COUNT} tenders, expect HIGH HHI (~85% single-vendor win rate)")
    print("                                            + narrow eligibility text overlap on a subset")
    print(f"  - Health Dept / Medical Supplies       -> {MEDICAL_SUPPLIES_COUNT} tenders, expect MODERATE HHI (50/30/20 split)")
    print("                                            + ~12 deliberate single-bidder tenders")
    print(f"  - Water Board / Pipeline Maintenance   -> {PIPELINE_MAINTENANCE_COUNT} tenders, expect LOW HHI (5 vendors, near-even)")
    print(f"  - Education Dept / School Furniture    -> {SCHOOL_FURNITURE_COUNT} tenders, expect MODERATE-HIGH HHI (~65/35 split)")
    print("                                            (gray-zone case — tests threshold granularity)")


def main():
    engine = get_engine()
    with engine.begin() as conn:  # single transaction — all-or-nothing
        truncate_all(conn)
        seed(conn)


if __name__ == "__main__":
    main()
