-- AstaPS 7.1 compatibility reward gadget for fallback waves.
-- DomainRewardStatueHelper enables claiming only on successful completion.
local base_info = { group_id = 240771004 }
monsters = {}
npcs = {}
gadgets = {
    { config_id = 5001, gadget_id = 70350008, pos = { x = 0.000, y = 0.150, z = -28.000 }, rot = { x = 0.000, y = 180.000, z = 0.000 }, level = 1, state = 0 }
}
regions = {}
triggers = {}
variables = {}
init_config = { suite = 1, end_suite = 0, rand_suite = false }
suites = {
    { monsters = {}, gadgets = {5001}, regions = {}, triggers = {}, rand_weight = 100 }
}
