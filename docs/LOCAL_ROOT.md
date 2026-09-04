# Going local: rooting the hub and installing the bridge

This is the Phase 2 hardware path. It is **optional**, the integration works
today over the cloud with no hardware changes. Do this when you want the bed to
keep working after the SleepIQ cloud is gone, and to recover the base/foundation
control that Sleep Number has already cut server-side.

> ⚠️ Opening the hub and touching the UART pins is at your own risk and may void
> any remaining warranty. Only you can perform this step; the software here
> cannot. Read the whole page before starting.

## Why this is necessary

A stock SleepIQ hub (model **360SIQ01D**) exposes **no** local network service -
verified on this bed: zero open TCP ports, no UPnP, no mDNS. It only talks
outbound to the cloud. To get a local data path you install a small bridge
daemon on the hub, and to install anything you first need a root shell, which
the hub only offers over its serial console.

Credit: the root method below is based on the excellent write-up by
[Dillan Mills](https://dillan.org/articles/how-to-get-root-access-to-your-sleep-number-bed).

## 1. Hardware

- A **3.3 V USB-to-UART adapter** (FTDI / CP2102 / CH340). **Do not use 5 V.**
- The hub's **J16** header (10-pin). Pinout used here:
  - **Pin 1** – TX (into hub)
  - **Pin 2** – RX (out of hub)
  - **Pin 3** – GND
- Console settings: **115200 baud, 8N1**, this is the "negotiate baud / serial
  connection" work at the center of the project; for SleepIQ the serial line is
  the hub's own console and the baud is fixed by U-Boot.

Wire adapter TX→hub RX, adapter RX→hub TX, GND→GND. Open a serial terminal at
115200 8N1.

## 2. Interrupt U-Boot and get a shell

Power the hub. Within the ~2 second window, press a key to stop autoboot at the
U-Boot prompt, then boot to a shell instead of the normal init:

```
setenv bootcmd 'run set_bootargs; ...'      # inspect existing bootcmd first
# Boot to a raw shell, bypassing the encrypted init gate:
setenv bootargs 'console=ttymxc0,115200 root=/dev/mmcblk${linux_mmcdev}p1 rootwait rdinit=/bin/bash -- -c "sed -i \'s/LMR=`.*`/LMR=let_me_root/\' /init; exec /init"'
boot
```

You now have a root shell. See Dillan's article for the full explanation of the
`LMR` gate and how to make root persistent by mounting `/dev/mmcblk0p1` and
editing the on-disk `/real.root` outside the chroot.

## 3. Install the bridge

Copy `bridge/sleepnumber_bridge.py` to the hub (e.g. `/bam/sleepnumber_bridge.py`)
via your serial session or, once networking is up, `scp`. Then confirm the hub's
local command tool path, the vendor script that speaks to the pump (Dillan's is
at `/bam/scripts/bio`). Point the bridge at it and start it:

```sh
export SNB_CMD="/bam/scripts/bio {key} {arg}"   # adjust to your hub's tool
export SNB_PORT=8765
export SNB_TOKEN="choose-a-shared-secret"        # optional but recommended
python /bam/sleepnumber_bridge.py &
```

Verify from another machine on the LAN:

```sh
curl -H "X-SNB-Token: choose-a-shared-secret" http://<hub-ip>:8765/health
curl -H "X-SNB-Token: choose-a-shared-secret" http://<hub-ip>:8765/status
```

Make it start on boot with an init.d entry (the hub uses SysV rc.d; add a script
under `/etc/init.d/` and symlink into `rc3.d`/`rc5.d`). Keep a copy on the
persistent partition so a firmware refresh doesn't wipe it.

## 4. Point Home Assistant at the hub

Once the bridge answers on the LAN, the integration's local transport
(`custom_components/sleepnumber_pro/local.py`) prefers it automatically when a
hub host is configured, and falls back to the cloud if it ever stops answering.

## Protocol reference (4-letter keys)

The bridge passes these through to the hub's pump tool. Confirmed/derived from
the vendor command table and the root write-up:

| Key | Meaning | Notes |
|-----|---------|-------|
| `PSNL` / `PSNR` | Read sleep number, left / right | |
| `PSNS` | Set sleep number | arg like `L100` |
| `LBPL` / `LBPR` | In-bed presence, left / right | |
| `MFUL` / `MFFL` | Head / foot position | base articulation |
| `FWSL` | Foot warming | if fitted |
| `SBAS` | Calibrate / baseline | |

The exact stdout format of your hub's tool may differ; `local.py`'s parser is
deliberately lenient (extracts digits / recognises common truthy words). Capture
a few `/raw?key=PSNL` responses and tighten the parser to match if needed.
