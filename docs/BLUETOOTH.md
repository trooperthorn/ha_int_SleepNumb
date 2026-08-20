# Bluetooth LE: the no-root local path

The Sleep Number smart hub has its **own Bluetooth LE radio** — it's how the
Sleep Number app controls the bed when you're near it. That makes BLE the
**least-invasive local transport**: unlike the on-hub bridge, it needs no UART
root and no opening the hub. It just needs a Bluetooth adapter within range of
the bed (the app requires ~8 ft / BLE 4.0).

This is why the integration treats transports in this order:

1. **Bluetooth LE** — local, no hardware modification, in-range only.
2. **On-hub bridge** — local, whole-home, requires a one-time UART root
   (see [`LOCAL_ROOT.md`](LOCAL_ROOT.md)).
3. **Cloud** — fallback, works everywhere until Sleep Number shuts it down.

## What's known

- Sleep Number smart hubs advertise a **custom GATT service**
  `09d23fae-90e6-44c2-95b6-0b3d0f1abf25` (observed on the Climate 360) containing
  several **read / write / notify** characteristics — so BLE supports both
  reading status and sending commands, not just fire-and-forget control.
- The community has reverse-engineered the SleepIQ app's BLE protocol for local
  control (left/right firmness presets, under-bed light, with presence detection
  in progress). The exact characteristic-to-function mapping and command bytes
  vary by model and firmware.
- Generic adjustable-base projects (`smartbed-mqtt`, `ha-adjustable-bed`) cover
  Richmat / Keeson / Okin / Linak controllers but **not** Sleep Number's own
  protocol — Sleep Number gates the base behind its hub.

## Capture your bed's GATT

Because UUIDs and command bytes differ by model, the next step is to capture
**your** bed's table. Two ways:

- **This repo's tool** (needs a BT adapter near the bed):
  ```
  pip install bleak
  python tools/ble_scan.py            # find the bed's BLE address
  python tools/ble_scan.py <ADDRESS>  # dump every service + characteristic
  ```
- **Phone app**: nRF Connect (iOS/Android) — connect to the bed and browse the
  GATT services; export the log.

Record: the service UUID, each characteristic UUID and its properties
(read/write/notify), and — by toggling functions in the Sleep Number app while
sniffing — which writes map to which actions.

## Using BLE from Home Assistant

Home Assistant discovers the bed over BLE automatically (the integration
declares the service UUID in its manifest) and stores the BLE address on the
config entry. To actually reach the radio you need one of:

- A **Bluetooth adapter on the HA host**, within range of the bed, or
- An **ESP32 running ESPHome's Bluetooth Proxy** near the bed (the standard HA
  pattern for out-of-range BLE devices). Note only one connection can use an
  ESP32 proxy's radio at a time.

## Status in this integration

- ✅ BLE **discovery** (manifest matcher + config-flow `bluetooth` step) — the
  bed is recognised and its address recorded.
- 🔶 BLE **transport** (read/write over the characteristics) — scaffolded; needs
  your captured GATT to finish the command map. Once captured, it slots in ahead
  of the bridge and cloud in the coordinator, exactly like the local bridge does.
