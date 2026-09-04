# Bluetooth LE: the no-root local path

The Sleep Number smart hub has its **own Bluetooth LE radio**, it's how the
Sleep Number app controls the bed when you're near it. That makes BLE the
**least-invasive local transport**: unlike the on-hub bridge, it needs no UART
root and no opening the hub. It just needs a Bluetooth adapter within range of
the bed (the app requires ~8 ft / BLE 4.0).

This is why the integration treats transports in this order:

1. **Bluetooth LE**, local, no hardware modification, in-range only.
2. **On-hub bridge**, local, whole-home, requires a one-time UART root
   (see [`LOCAL_ROOT.md`](LOCAL_ROOT.md)).
3. **Cloud**, fallback, works everywhere until Sleep Number shuts it down.

## Confirmed on this hub (360-gen, 2026-08-20)

A live advertisement captured through a Home Assistant Bluetooth Proxy:

```json
{"address":"64:DB:A0:0C:1E:58","rssi":-80,"connectable":true,
 "manufacturer_data":{"20051":"9206000000"},
 "service_uuids":["ffffd1fd-388d-938b-344a-939d1f6efee0"],
 "source":"00:01:95:CC:31:70"}
```

- **Same MAC as the hub's Wi-Fi** (`64:DB:A0:0C:1E:58`), the BLE radio and the
  networked hub are one device.
- **`connectable: true`**: GATT connections are possible (via the proxy).
- **Manufacturer id `20051` = `0x4E53` = "SN"**, payload `92 06 00 00 00`. This
  small payload may encode live state, if it changes with presence or sleep
  number, HA can read it **passively from adverts, with no GATT connection**.
- **Service UUID `ffffd1fd-388d-938b-344a-939d1f6efee0`**: this 360-gen hub's
  service (the Climate 360 uses a different one). The integration matches both.

Practical notes for proxy use: RSSI **−80** is usable but marginal, put the
proxy closer to the bed for reliable connect/read/write. An ESP32 proxy holds
**one** active GATT connection at a time, so the bed occupies that slot while
connected.

## What's known

- Sleep Number smart hubs advertise a **custom GATT service** (confirmed
  `ffffd1fd-…` here; `09d23fae-…` on the Climate 360) containing several
  **read / write / notify** characteristics, so BLE supports both reading status
  and sending commands, not just fire-and-forget control.
- The community has reverse-engineered the SleepIQ app's BLE protocol for local
  control (left/right firmness presets, under-bed light, with presence detection
  in progress). The exact characteristic-to-function mapping and command bytes
  vary by model and firmware.
- Generic adjustable-base projects (`smartbed-mqtt`, `ha-adjustable-bed`) cover
  Richmat / Keeson / Okin / Linak controllers but **not** Sleep Number's own
  protocol, Sleep Number gates the base behind its hub.

## Capture your bed's GATT

Because UUIDs and command bytes differ by model, the next step is to capture
**your** bed's table. Two ways:

- **This repo's tool** (needs a BT adapter near the bed):
  ```
  pip install bleak
  python tools/ble_scan.py            # find the bed's BLE address
  python tools/ble_scan.py <ADDRESS>  # dump every service + characteristic
  ```
- **Phone app**: nRF Connect (iOS/Android), connect to the bed and browse the
  GATT services; export the log.

Record: the service UUID, each characteristic UUID and its properties
(read/write/notify), and, by toggling functions in the Sleep Number app while
sniffing, which writes map to which actions.

## Using BLE from Home Assistant

Home Assistant discovers the bed over BLE automatically (the integration
declares the service UUID in its manifest) and stores the BLE address on the
config entry. To actually reach the radio you need one of:

- A **Bluetooth adapter on the HA host**, within range of the bed, or
- An **ESP32 running ESPHome's Bluetooth Proxy** near the bed (the standard HA
  pattern for out-of-range BLE devices). Note only one connection can use an
  ESP32 proxy's radio at a time.

## The MCR protocol (implemented)

The `ffffd1fd-…` service is a UART-style channel speaking the **MCR** binary
protocol, the same BAM command family the cloud `bamkey` endpoint and the on-hub
`/bio` tool use. Two characteristics:

- `…fee2` **MCR RX**, `write` (client → bed): commands.
- `…fee1` **MCR TX**, `notify` (bed → client): responses.

Frame: `[0x16 0x16] + 10-byte header + payload + CRC16` (Fletcher-16 over
header+payload). Header carries a command class (`0x02` pump / `0x42` foundation),
the bed's MCR address (last two bytes of its MAC, e.g. `64:DB:A0:0C:1E:58` →
`0x1E58`), a function code, and a side/length byte. The codec lives in
[`mcr.py`](../custom_components/sleepnumber_pro/mcr.py) and is unit-tested against
the documented init vector.

Functions used: init handshake (0), read pump status (18 → `[pump_on, L_SN, R_SN,
L_pump, R_pump]`), set sleep number (17), foundation status (0x42/18 → head/foot
positions), activate preset (0x42/21). **Presence over MCR is firmware-broken
(always 0)**, so presence still comes from the cloud/pressure plane.

**Foundation control works over BLE even though the cloud severed it**, that's
what the *Base preset* select uses.

> **Proxy gotcha:** MCR RX advertises *write-without-response*, but through an
> ESPHome Bluetooth Proxy you **must** write **with** response, the proxy
> silently drops write-without-response packets. This integration always writes
> with response.

## Status in this integration

- ✅ BLE **discovery**, manifest matcher (service `ffffd1fd-…`, `09d23fae-…`,
  manufacturer id 20051) + config-flow `bluetooth` step records the bed's address.
- ✅ BLE **transport**, connect-on-demand via HA's Bluetooth stack, MCR
  handshake, read sleep number, set sleep number, foundation status, and base
  presets. Selected ahead of the on-hub bridge and cloud in the coordinator; the
  **Connection** sensor shows `Bluetooth` when it's live.
- 🔶 Head/foot *fine positioning* (raw foundation `SET`) is deferred pending safety
  validation; presets cover the common moves.

## Attribution

The MCR/BAM protocol was reverse-engineered by the community from the SleepIQ app.
This is an independent implementation from the public protocol notes; credit to
[`JonGilmore/sleepnumber-ble`](https://github.com/JonGilmore/sleepnumber-ble),
[`kristofferR/ha-adjustable-bed`](https://github.com/kristofferR/ha-adjustable-bed),
and [`canning1295/BedRemote`](https://github.com/canning1295/BedRemote) for
documenting the frame format and function codes.
