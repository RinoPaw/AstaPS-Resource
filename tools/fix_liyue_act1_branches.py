#!/usr/bin/env python3
from __future__ import annotations

import fix_liyue_prerequisites as base
from fix_quest_prerequisites import Repair, one, state_equal

# Liyue Act I branch / convergence extension.
#
# Evidence:
# - GCResource 3.7 and 4.0 agree on these prerequisite graphs.
# - Current 7.1 BinOutput has lost acceptCond on the corresponding subquests.
# - The flattened resource collapses fan-outs and compound gates into order chains.
#
# Importing the base module makes this script apply the already-audited
# 400 -> MQ1000 -> MQ1002 -> MQ1003 repairs in the same pass.
BRANCH_REPAIRS = (
    # MQ1008: 100801/100802/100803 fan out from 100808.
    Repair("1008.json", 1008, 100808, -1, one(100205), (one(0),)),
    Repair("1008.json", 1008, 100801, -1, one(100808), (one(100808),)),
    Repair("1008.json", 1008, 100802, -1, one(100808), (one(100801),)),
    Repair("1008.json", 1008, 100803, -1, one(100808), (one(100802),)),
    Repair(
        "1008.json",
        1008,
        100804,
        -1,
        (state_equal(100802), state_equal(100803, state=2)),
        (one(100803),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1008.json",
        1008,
        100805,
        -1,
        (state_equal(100803), state_equal(100804)),
        (one(100804),),
        expected_comb="LOGIC_OR",
    ),
    Repair("1008.json", 1008, 100806, -1, one(100805), (one(100805),)),
    Repair("1008.json", 1008, 100807, -1, one(100806), (one(100806),)),

    # MQ1009: fan out from 100915, then again from 100906.
    Repair("1009.json", 1009, 100901, -1, one(100205), (one(0),)),
    Repair("1009.json", 1009, 100915, -1, one(100901), (one(100901),)),
    Repair("1009.json", 1009, 100902, -1, one(100915), (one(100915),)),
    Repair("1009.json", 1009, 100903, -1, one(100915), (one(100902),)),
    Repair("1009.json", 1009, 100904, -1, one(100915), (one(100903),)),
    Repair("1009.json", 1009, 100905, -1, one(100915), (one(100904),)),
    Repair("1009.json", 1009, 100906, -1, one(100915), (one(100905),)),
    Repair("1009.json", 1009, 100907, -1, one(100906), (one(100906),)),
    Repair("1009.json", 1009, 100908, -1, one(100906), (one(100907),)),
    Repair("1009.json", 1009, 100909, -1, one(100906), (one(100908),)),
    Repair("1009.json", 1009, 100910, -1, one(100906), (one(100909),)),
    Repair("1009.json", 1009, 100911, -1, one(100906), (one(100910),)),
    Repair("1009.json", 1009, 100912, -1, one(100911), (one(100911),)),
    Repair("1009.json", 1009, 100913, -1, one(99902), (one(100912),)),
    Repair("1009.json", 1009, 100914, -1, one(100912), (one(100913),)),

    # MQ1018: convergence gate for all three investigation branches.
    Repair(
        "1018.json",
        1018,
        101801,
        -1,
        (state_equal(100317), state_equal(100807), state_equal(100914)),
        (one(0),),
        expected_comb="LOGIC_AND",
    ),
)

base.REPAIRS += BRANCH_REPAIRS


if __name__ == "__main__":
    raise SystemExit(base.main())
