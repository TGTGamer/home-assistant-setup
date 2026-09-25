# Install Home Assistant OS

The rebuild from Raspbian with Home Assistant in Docker to Home Assistant OS.
Run the scripts from a Linux machine with an SD card reader.

## Why rebuild instead of upgrading

The old system was Raspbian 10 (Buster), 32-bit, running Home Assistant
2023.5 in Docker. Buster no longer gets updates, and Home Assistant stopped
building 32-bit ARM images in late 2025, so the old install could not reach a
current release. Home Assistant OS on the 64-bit image gives one-click updates,
built-in backups and apps.

## 1. Back up the old card

Before anything else, while the old system still runs:

1. Home Assistant: Settings, System, Backups, create and download a backup.
2. Shut the Pi down and move the card to the PC.
3. Copy the whole card to an image (about 30 GB):

   ```sh
   scripts/pi-flash.sh list                                   # find the card, for example /dev/sdd
   scripts/pi-flash.sh backup /dev/sdX ~/pi-backup-$(date +%F).img
   ```

Keep the old card untouched in a drawer; it and the image are the way back.

## 2. Write HA OS to the new card

Insert the new card, find it with `scripts/pi-flash.sh list`, and run:

```sh
scripts/pi-flash.sh flash /dev/sdX   # downloads the latest rpi4-64 image
```

It only accepts a removable disk, and asks you to type the device path again
before erasing it.

## 3. Add the boot settings

With the freshly written card still inserted:

```sh
scripts/prepare-boot.sh
```

This appends [`config.txt.append`](../ha-os/boot/config.txt.append) (RaspBee
UART, Bluetooth on the mini UART, I2C) and copies the `CONFIG` folder that
loads the I2C modules. Rerunning it changes nothing.

## 4. First boot

1. Card in the Pi, Ethernet plugged in, power on.
2. Wait up to 20 minutes, then open `http://homeassistant.local:8123`.
3. Onboard as a new install (not a restore; the old setup is being rebuilt
   rather than copied).

## 5. Access

1. Settings, Apps: install **Advanced SSH & Web Terminal**. Add your public
   key; keep any password in Proton Pass.
2. Check I2C on the host. The SSH app's terminal runs in its own container,
   which does not see `/dev/i2c-1`, so ask the Supervisor instead:
   `ha hardware info | grep i2c` should list `/dev/i2c-1`. Only if it does not,
   install the **HassOS I2C Configurator** app and reboot the host twice.

## 6. Zigbee

1. Settings, Apps: install **deCONZ**, set the device to `/dev/ttyAMA0`, start
   it and open the Phoscon web UI.
2. Settings, Devices and services: add the **deCONZ** integration.

## 7. Remote access and voice

Install [Homeway](https://homeway.io) (Home Assistant app). It provides remote
access, Google Assistant and Alexa linking, and an MCP endpoint for AI tools.

## 8. Hardware extras

1. HACS, then the UPS Plus integration; add an automation that shuts the host
   down cleanly when the battery gets low.
2. Add this repository in the App store and install **OLED Status** (see its
   [docs](../oled_status/DOCS.md)).

## 9. Integrations

Rebuild from [the previous setup checklist](previous-setup.md): add only what
is still used.
