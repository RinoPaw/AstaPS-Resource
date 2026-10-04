#!/usr/bin/env python3
from __future__ import annotations

import fix_liyue_prerequisites as base
from fix_quest_prerequisites import Repair, one, state_equal

# Early Liyue branch / convergence repairs through Chapter 1102.
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

    # MQ1010: Chapter 1102 entry after the three-branch convergence.
    # 101004 is an independent hidden controller rooted at 99902; the flattened
    # order chain incorrectly makes 101007 depend on it.
    Repair("1010.json", 1010, 101001, -1, one(101801), (one(0),)),
    Repair("1010.json", 1010, 101002, -1, one(101001), (one(101001),)),
    Repair("1010.json", 1010, 101003, -1, one(101002), (one(101002),)),
    Repair("1010.json", 1010, 101004, -1, one(99902), (one(101003),)),
    Repair("1010.json", 1010, 101007, -1, one(101003), (one(101004),)),
    Repair("1010.json", 1010, 101008, -1, one(101007), (one(101007),)),
    Repair("1010.json", 1010, 101005, -1, one(101008), (one(101008),)),
    Repair("1010.json", 1010, 101006, -1, one(101005), (one(101005),)),

    # MQ1011: Chapter 1102 incense / cleansing sequence.
    # 101127 is a hidden progress controller. Many sibling steps require both a
    # concrete predecessor to be FINISHED and 101127 to remain ACTIVE (state 2).
    Repair("1011.json", 1011, 101101, -1, one(101006), (one(0),)),
    Repair("1011.json", 1011, 101116, -1, one(101101), (one(101101),)),
    Repair("1011.json", 1011, 101102, -1, one(101101), (one(101116),)),
    Repair("1011.json", 1011, 101103, -1, one(101102), (one(101102),)),
    Repair("1011.json", 1011, 101112, -1, one(101103), (one(101103),)),
    Repair("1011.json", 1011, 101104, -1, one(101112), (one(101112),)),
    Repair("1011.json", 1011, 101128, -1, one(101112), (one(101104),)),
    Repair(
        "1011.json",
        1011,
        101105,
        -1,
        (state_equal(101104), state_equal(101127, state=2)),
        (one(101128),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101123,
        -1,
        (state_equal(101104), state_equal(101127, state=2)),
        (one(101105),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101113,
        -1,
        (state_equal(101123), state_equal(101127, state=2)),
        (one(101123),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101124,
        -1,
        (state_equal(101104), state_equal(101127, state=2)),
        (one(101113),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101114,
        -1,
        (state_equal(101124), state_equal(101127, state=2)),
        (one(101124),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101125,
        -1,
        (state_equal(101104), state_equal(101127, state=2)),
        (one(101114),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101115,
        -1,
        (state_equal(101125), state_equal(101127, state=2)),
        (one(101125),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101126,
        -1,
        (state_equal(101104), state_equal(101127, state=2)),
        (one(101115),),
        expected_comb="LOGIC_AND",
    ),
    Repair(
        "1011.json",
        1011,
        101106,
        -1,
        (state_equal(101126), state_equal(101127, state=2)),
        (one(101126),),
        expected_comb="LOGIC_AND",
    ),
    Repair("1011.json", 1011, 101127, -1, one(101104), (one(101106),)),
    Repair("1011.json", 1011, 101110, -1, one(101127), (one(101127),)),
    Repair("1011.json", 1011, 101111, -1, one(101127), (one(101110),)),
    Repair("1011.json", 1011, 101107, -1, one(101127), (one(101111),)),
    Repair("1011.json", 1011, 101108, -1, one(101107), (one(101107),)),
    Repair("1011.json", 1011, 101109, -1, one(101108), (one(101108),)),
)

base.REPAIRS += BRANCH_REPAIRS


if __name__ == "__main__":
    raise SystemExit(base.main())
