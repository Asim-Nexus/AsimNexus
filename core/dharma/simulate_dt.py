
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

import logging
logger = logging.getLogger(__name__)
"""
core/dharma/simulate_dt.py
DeltaT Engine v2 Simulation -- AsimNexus Dharma-Chakra

Run:  python -m core.dharma.simulate_dt
      python core/dharma/simulate_dt.py

Jay Dharma-Chakra
"""

import sys
sys.path.insert(0, ".")

from core.dharma.delta_t_engine import DeltaTEngine, run_pos_simulator

SEP  = "-" * 70
SEP2 = "=" * 70


def _make_engine_18() -> DeltaTEngine:
    """18-node realistic network. Fair share ~5.6%, L_max=7%."""
    e = DeltaTEngine(L_max=0.07, lambda_factor=8.0)
    normal = [
        ("farmer_01",    1200,  45,  92), ("farmer_02",    1100,  38,  88),
        ("farmer_03",    1350,  52,  85), ("local_shop_1", 2200,  90,  75),
        ("local_shop_2", 1900,  80,  72), ("local_shop_3", 2400,  95,  78),
        ("citizen_a",     800,  30,  65), ("citizen_b",     750,  28,  60),
        ("citizen_c",     900,  35,  70), ("school_node",  1500,  55,  95),
        ("hospital_node",1800,  65,  97), ("community_hub",2000,  75,  90),
        ("startup_x",    3000, 110,  68), ("startup_y",    2800,  98,  71),
        ("cooperative",  1600,  60,  82),
    ]
    for nid, res, tx, rep in normal:
        e.register_node(nid, resources=res, tx_rate=tx, rep_score=rep)
    e.register_node("local_company", resources=8500,  tx_rate=280, rep_score=65)
    e.register_node("regional_corp", resources=12000, tx_rate=420, rep_score=58)
    return e


def print_summary(engine: DeltaTEngine, title: str) -> None:
    s = engine.network_summary()
    logger.info("\n" + SEP)
    logger.info("  " + title)
    print(SEP)
    print("  Nodes: {}  |  L_max={:.0f}%  |  symmetry={:.3f}  gini={:.3f}  [{}]".format(
        s["node_count"], s["L_max"] * 100,
        s["symmetry_score"], s["gini_coefficient"], s["verdict"]
    ))
    print("  {:<20} {:>7} {:>8}  Status".format("Node", "ratio", "DT"))
    print("  {:<20} {:>7} {:>8}  ------".format("----", "-----", "--"))
    for nid, nd in s["nodes"].items():
        icon = "[VETO]" if nd["cap_violated"] else "[OK]  "
        print("  {:<20} {:>6.1f}%  {:>+.3f}  {}".format(
            nid, nd["ratio_pct"], nd["delta_t"], icon
        ))


def run_cycle_report(engine: DeltaTEngine) -> None:
    pos = engine.run_cycle()
    s = engine.network_summary()
    viol = sum(1 for n in s["nodes"].values() if n["cap_violated"])
    if viol:
        print("  [VETO] {} violation(s) | symmetry={:.3f} [{}]".format(
            viol, pos.symmetry_score, pos.verdict))
    else:
        print("  [OK] No violations | symmetry={:.3f} [{}]".format(
            pos.symmetry_score, pos.verdict))


def scenario_1_balanced() -> None:
    logger.info("\n" + SEP2)
    print("  SCENARIO 1: Balanced 18-node network (no violations expected)")
    print(SEP2)
    engine = _make_engine_18()
    run_cycle_report(engine)
    print_summary(engine, "Network state after 1 cycle")


def scenario_2_blackrock() -> None:
    logger.info("\n" + SEP2)
    print("  SCENARIO 2: BlackRock-style monopoly capture (external_corp)")
    print(SEP2)
    engine = _make_engine_18()
    engine.register_node("external_corp", resources=45000, tx_rate=1250, rep_score=88)
    print("  18 + 1 monopoly node. external_corp raw resource share ~55%")
    for i in range(1, 4):
        pos = engine.run_cycle()
        nd = engine.network_summary()["nodes"]["external_corp"]
        print("  Cycle {}: external_corp ratio={:.1f}%  cap_violated={}  PoS=[{}]".format(
            i, nd["ratio_pct"], nd["cap_violated"], pos.verdict))
    print_summary(engine, "After 3 cycles of attenuation")


def scenario_3_recovery() -> None:
    logger.info("\n" + SEP2)
    print("  SCENARIO 3: Recovery -- dominant node reduces, symmetry improves")
    print(SEP2)
    engine = _make_engine_18()
    engine.register_node("dominant", resources=40000, tx_rate=1000, rep_score=80)

    print("  Step 1: dominant at full power:")
    run_cycle_report(engine)

    engine.register_node("dominant", resources=5000, tx_rate=100, rep_score=70)
    print("  Step 2: dominant voluntarily reduces:")
    run_cycle_report(engine)

    engine.register_node("dominant", resources=2000, tx_rate=60, rep_score=65)
    print("  Step 3: fully balanced:")
    run_cycle_report(engine)


def main() -> None:
    logger.info("\n" + SEP2)
    logger.info("  AsimNexus -- DeltaT Engine v2 Simulation")
    logger.info("  Dharma-Chakra Anti-Concentration System")
    print("  Jay Dharma-Chakra")
    print(SEP2)

    scenario_1_balanced()
    scenario_2_blackrock()
    scenario_3_recovery()

    logger.info("\n" + SEP2)
    print("  --- Built-in PoS Simulator (Chief Architect original design) ---")
    print(SEP2)
    run_pos_simulator()

    logger.info("\n" + SEP2)
    logger.info("  Simulation complete. DeltaT Engine v2 working correctly.")
    print("  Next: /api/dharma/status in simple_backend.py")
    print(SEP2)


if __name__ == "__main__":
    main()
