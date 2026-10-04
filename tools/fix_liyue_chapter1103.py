#!/usr/bin/env python3
from __future__ import annotations

import fix_liyue_chapter1102  # noqa: F401 - extends the shared manifest on import
import fix_liyue_prerequisites as base
from fix_quest_prerequisites import Repair, one, state_equal

# Liyue Chapter 1103 prerequisite repairs.
#
# Evidence:
# - GCResource 3.7 and 4.0 are byte-identical for MQ1020 and MQ1021.
# - Current 7.1 BinOutput has lost the subquest acceptCond graph.
# - The flattened resource synthesizes order-based predecessor edges, corrupting
#   roots, fan-outs and the three-way convergence gate in MQ1021.
CHAPTER_1103_REPAIRS = (
    # MQ1020: Chapter 1103 entry. Historical graph is linear; source still needs
    # full restoration while only the root is semantically wrong after flattening.
    Repair("1020.json", 1020, 102001, -1, one(101610), (one(0),)),
    Repair("1020.json", 1020, 102002, -1, one(102001), (one(102001),)),
    Repair("1020.json", 1020, 102003, -1, one(102002), (one(102002),)),
    Repair("1020.json", 1020, 102007, -1, one(102003), (one(102003),)),
    Repair("1020.json", 1020, 102004, -1, one(102007), (one(102007),)),
    Repair("1020.json", 1020, 102005, -1, one(102004), (one(102004),)),
    Repair("1020.json", 1020, 102006, -1, one(102005), (one(102005),)),

    # MQ1021: three parallel preparations fan out from 102006 and reconverge at
    # 102111. Flattening turns the fan-out into an order chain and drops the
    # three-way AND gate.
    Repair("1021.json", 1021, 102109, -1, one(102006), (one(0),)),
    Repair("1021.json", 1021, 102110, -1, one(102006), (one(102109),)),
    Repair("1021.json", 1021, 102101, -1, one(102006), (one(102110),)),
    Repair("1021.json", 1021, 102102, -1, one(102101), (one(102101),)),
    Repair("1021.json", 1021, 102107, -1, one(102102), (one(102102),)),
    Repair("1021.json", 1021, 102108, -1, one(102107), (one(102107),)),
    Repair(
        "1021.json",
        1021,
        102111,
        -1,
        (state_equal(102109), state_equal(102110), state_equal(102108)),
        (one(102108),),
        expected_comb="LOGIC_AND",
    ),
    Repair("1021.json", 1021, 102103, -1, one(102111), (one(102111),)),
    Repair("1021.json", 1021, 102104, -1, one(102103), (one(102103),)),
    Repair("1021.json", 1021, 102113, -1, one(102104), (one(102104),)),
    Repair("1021.json", 1021, 102105, -1, one(102113), (one(102113),)),
    Repair("1021.json", 1021, 102106, -1, one(102105), (one(102105),)),
    Repair("1021.json", 1021, 102112, -1, one(102106), (one(102106),)),
)

base.REPAIRS += CHAPTER_1103_REPAIRS


if __name__ == "__main__":
    raise SystemExit(base.main())
