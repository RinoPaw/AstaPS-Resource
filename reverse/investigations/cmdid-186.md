# Genshin 7.1 CmdId 186 investigation

Status: `observed-unresolved`

## Runtime observation

During fresh-account born/login tracing, the 7.1 Windows client sent:

- CmdId: `186` (`0xBA`)
- Direction: client -> server
- Payload: `72 02 d0 27`

The observation occurred during the intro/login window after born data had been accepted. No semantic packet name has been assigned yet.

## Payload structure

A protobuf wire-level reading of `72 02 d0 27` gives:

- `0x72`: field 14, wire type 2 (length-delimited)
- `0x02`: length 2
- body: `d0 27`

If that two-byte body is a packed varint, it decodes to `5072`. That interpretation is only a hypothesis; field 14 may also be bytes or a nested message.

## Historical collision warning

Some old Genshin mappings used numeric CmdId 186 for `PlayerPropChangeNotify`. CmdIds changed across later versions, so this historical equality is evidence only for old clients and must not be copied into the 7.1 mapping.

## Static recovery plan

Use the matching 7.1 Windows executable and metadata sample:

1. Locate packet classes/functions whose `GetCmdId()` returns `0xBA`.
2. Recover the containing class/vtable and parser path.
3. Identify the corresponding protobuf/message layout.
4. Check whether field 14 can produce the observed body `d0 27`.
5. Trace call sites to the intro/login state where the runtime packet was observed.
6. Only after the static and runtime evidence agree, rename `UNKNOWN_186` in the 7.1 observation table.

Matching metadata fingerprint:

`sha256:05ae04d7a91b91cc880217a56b0b01f3e67f845b06e894216654ec5d160e0da0`
