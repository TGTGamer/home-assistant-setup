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

It only accepts a removable disk up to 256 GB, and asks you to type the device
path again before erasing it. `backup` never replaces an existing image file.

## 3. Add the boot settings

With the freshly written card still inserted:

```sh
scripts/prepare-boot.sh
```

This appends [`config.txt.append`](../ha-os/boot/config.txt.append) (RaspBee
UART, Bluetooth on the mini UART, I2C) and copies the `CONFIG` folder that
loads the I2C modules. Rerunning it changes nothing.

### Changing boot settings later

The boot partition is not visible from the SSH app, so on a running hub:

1. Install **Advanced SSH & Web Terminal** temporarily, with your key, a spare
   SSH port (for example 2222) and **Protection mode** off, which gives it
   Docker access to the host.
2. Mount the boot partition in a short-lived privileged container, back up
   `config.txt`, then edit it:

   ```sh
   docker run --rm --privileged -v /dev:/dev --entrypoint sh \
     ghcr.io/home-assistant/aarch64-hassio-supervisor:<version> -c \
     "mkdir -p /mnt/boot && mount -t vfat /dev/mmcblk0p1 /mnt/boot \
      && cp /mnt/boot/config.txt /mnt/boot/config.txt.bak && vi /mnt/boot/config.txt; umount /mnt/boot"
   ```

3. **Uninstall the Advanced SSH app** so host access does not stay open, then
   `ha host reboot`.

## 4. First boot

1. Card in the Pi, Ethernet plugged in, power on.
2. Wait up to 20 minutes, then open `http://homeassistant.local`. On this
   install Home Assistant answers on port 80 rather than the usual 8123; try
   both if one does not load.
3. Onboard as a new install (not a restore; the old setup is being rebuilt
   rather than copied).

## 5. Access

1. Settings, Apps: install the official **Terminal & SSH** app. Add your public
   key to `authorized_keys` and leave the password empty. Keep the key in
   Proton Pass (`pass-cli item create ssh-key generate`, then
   `pass-cli ssh-agent load`).
2. In the app's **Network** settings, set the SSH port to `22`. Until a port is
   set the app is only the in-browser terminal, and SSH from another machine
   is refused.
3. Start it with **Start on boot** on, then `ssh root@homeassistant.local`.
   The first connection shows a new host key; that is expected after a
   rebuild, so remove the old entry with `ssh-keygen -R <address>`.
4. Check the boot settings worked: `ha hardware info` should list
   `/dev/i2c-1` (OLED and UPS) and `/dev/ttyAMA0` (RaspBee II). The SSH
   container cannot see these devices itself, so ask the Supervisor.
5. For scripted access, create a long-lived access token (your profile,
   Security) and keep it in Proton Pass; reference it from an env file as
   `HA_TOKEN=pass://...` and run tools through `pass-cli run --env-file`.

## 6. Zigbee

1. Settings, Apps: install **deCONZ**, set the device to `/dev/ttyAMA0`, turn
   on **Start on boot** and start it.
2. On a fresh install deCONZ announces itself to Home Assistant before its
   database exists, so the integration may not be offered. Restart the app
   once; its log then shows "Successfully sent discovery information", and
   Settings, Devices and services offers **deCONZ**.
3. Open the Phoscon web UI from the app. First run asks you to **create** a
   gateway name and password; save the password in Proton Pass. Home Assistant
   uses its own API key, not this password. Never choose to reset the gateway
   or create a new network: the RaspBee keeps the existing Zigbee network.

## 7. Remote access and voice

1. Settings, Apps, App store, Repositories: add
   `https://github.com/homewayio/AddOn` and install **Homeway**.
2. Start it. On first start it enables trusted-proxy settings and restarts
   Home Assistant once; that is expected.
3. Open the link from the app's log to connect it to your Homeway account.
   Remote access, Google Assistant and Alexa linking, and the MCP endpoint are
   then managed from the Homeway dashboard.

## 8. Hardware extras

### HACS

1. Download `hacs.zip` from the latest
   [HACS release](https://github.com/hacs/integration/releases) and unzip it
   into `/homeassistant/custom_components/hacs`, then restart Home Assistant.
2. Settings, Devices and services, add **HACS**, accept the four
   acknowledgements, and approve the code at https://github.com/login/device
   within 15 minutes.

### UPS Plus

1. HACS: download **UPS Plus** (`archef2000/homeassistant-upsplus`), restart
   Home Assistant, then add the **UPS Plus** integration. Leave "advanced"
   off, so it writes nothing to the UPS. Its "automatic shutdown" setting is
   stored but not acted on, so the shutdown is an automation instead.
2. Add a template binary sensor **UPS mains power** (`device_class: plug`):
   on when the USB-C or micro-USB input is above 4.5 V, and unknown while the
   UPS readings are unavailable (template in the automations file).
3. Add the automations in [`ha-config/automations/ups.yaml`](../ha-config/automations/ups.yaml):
   a notification when the hub changes power source, a clean
   `hassio.host_shutdown` when the battery is below 25% or 3.75 V while mains
   is off (before the UPS cuts power at its 3.7 V protection voltage), and a
   reload after a failed boot read.
4. The UPS can miss its first I2C read at boot, leaving every UPS sensor
   unavailable. The third automation reloads the integration when that
   happens.
5. Turn on **UPS Turn on after power on**, so the Pi starts again when mains
   returns after a low-battery shutdown.

### OLED Status

Add this repository in the App store and install **OLED Status** (see its
[docs](../oled_status/DOCS.md)). Point `ups_battery` at
`sensor.ups_battery_capacity` and `ups_charging` at
`binary_sensor.ups_mains_power`.

## 9. Integrations

Rebuild from [the previous setup checklist](previous-setup.md): add only what
is still used.
