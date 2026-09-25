# Hardware

## Home hub

| Part | Role | On Home Assistant OS |
| --- | --- | --- |
| Raspberry Pi 4 Model B, 8 GB | The hub | Supported; use the 64-bit `rpi4-64` image |
| GeeekPi mini tower case with ICE Tower cooler and PWM RGB fan | Cooling | Fan runs from the 5 V pins, nothing to configure |
| 52Pi / GeeekPi UPS Plus (EP-0136) | Battery backup | Talks I2C at `0x17`; needs I2C on. Community integration: [archef2000/homeassistant-upsplus](https://github.com/archef2000/homeassistant-upsplus) via HACS |
| 0.96 inch SSD1306 OLED, 128x64 | Status screen | I2C at `0x3C`; driven by the [OLED Status](../oled_status/DOCS.md) app |
| GPIO 1-to-2 expansion board | Lets the UPS, OLED and RaspBee share the header | Nothing to configure |
| Phoscon RaspBee II | Zigbee 3.0 radio on the GPIO UART | Serial port `/dev/ttyAMA0`, radio type `deconz`. Needs the full UART (see below) |
| 32 GB and 64 GB SanDisk microSD cards | Storage | 64 GB runs HA OS; the old 32 GB card is kept as a backup |

### Why the boot settings matter

The Pi 4 has one full UART, which Bluetooth uses by default. The RaspBee II
needs it, so `dtoverlay=miniuart-bt` moves Bluetooth to the mini UART, and
`core_freq=250` fixes the core clock the mini UART's timing depends on. I2C is
off by default and HA OS has no `raspi-config`, so `config.txt` turns it on and
`CONFIG/modules/rpi-i2c.conf` loads the kernel modules. Both live in
[`ha-os/boot`](../ha-os/boot) and `scripts/prepare-boot.sh` applies them.

### Zigbee software

The RaspBee II is the radio whichever software drives it. The plan keeps the
**deCONZ app with Phoscon** (official Home Assistant app) for continuity. ZHA
and Zigbee2MQTT use the same radio and remain options later; only one can use
it at a time.

### Z-Wave

The RaspBee II is Zigbee only. Z-Wave needs a separate USB stick for the UK/EU
frequency (for example Home Assistant ZWA-2, Zooz ZST39 LR or Aeotec Z-Stick 7)
driven by the Z-Wave JS app. Not bought yet.

## Other hardware

| Part | Plan |
| --- | --- |
| Raspberry Pi 3 B+ | Wall or desk panel: Raspberry Pi OS Lite with Chromium in kiosk mode on a Home Assistant dashboard |
| Raspberry Pi 7 inch touch display | The panel's screen |
