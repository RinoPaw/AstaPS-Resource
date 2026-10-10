-- AstaPS 7.1 compatibility reward gadget for fallback waves.
-- DomainRewardStatueHelper enables claiming only on successful completion.
local base_info = { group_id = 240773004 }
monsters = {}
npcs = {}
gadgets = {
    -- 40773's native reward group is unavailable. Keep the verified 40501
    -- two-piece relationship, anchored to the 40773 fallback reward point
    -- at z=-28. The 70350008 accessory is not an interaction target.
    { config_id = 5001, gadget_id = 70340012, pos = { x = 0.300, y = 0.150, z = -28.000 }, rot = { x = 0.000, y = 0.000, z = 0.000 }, level = 1 },
    { config_id = 5002, gadget_id = 70350008, pos = { x = 0.412, y = 4.111, z = -23.817 }, rot = { x = 0.000, y = 0.000, z = 0.000 }, level = 1 }
}
regions = {}
triggers = {
    { config_id = 1005003, name = "DUNGEON_SETTLE_5003",
      event = EventType.EVENT_DUNGEON_SETTLE, source = "",
      condition = "condition_EVENT_DUNGEON_SETTLE_5003",
      action = "action_EVENT_DUNGEON_SETTLE_5003" }
}
variables = {}
init_config = { suite = 1, end_suite = 0, rand_suite = false }
suites = {
    { monsters = {}, gadgets = {5001, 5002}, regions = {}, triggers = {"DUNGEON_SETTLE_5003"}, rand_weight = 100 }
}

function condition_EVENT_DUNGEON_SETTLE_5003(context, evt)
    return evt.param1 == 1
end

function action_EVENT_DUNGEON_SETTLE_5003(context, evt)
    return ScriptLib.SetGadgetStateByConfigId(context, 5001, GadgetState.StatueActive)
end
