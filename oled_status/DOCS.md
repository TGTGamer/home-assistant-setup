# OLED Status

Shows what matters about the house on the 0.96 inch 128x64 SSD1306 OLED of a
Raspberry Pi case, and interrupts itself when something needs attention.

![All pages](https://raw.githubusercontent.com/TGTGamer/home-assistant-setup/main/docs/images/oled-pages.png)

## Pages

| Page | Shows | Shown when |
| --- | --- | --- |
| `clock` | Time, date, weather icon | Always |
| `weather` | Condition icon, temperature | `weather` is set |
| `people` | Who is home | `persons` is set |
| `locks` | Each lock and its state | `locks` is set |
| `heating` | Current and target temperature; flame flickers while heating | `climate` is set |
| `bins` | Next collections | `bins` is set and a collection is due |
| `media` | Title (scrolling) and artist | `media_player` is playing |
| `ups` | Battery level, mains or battery | `ups_battery` is set |
| `mood` | A face: happy when all is well, worried when there are alerts | Always |
| `starfield` | Animated stars, which also spares the OLED from burn-in | Always |

Pages with nothing to show are skipped. If none are left, the clock shows.

## Alerts

Alerts take every other slot in the rotation until they clear. The most
urgent one is shown first; critical alerts flash.

| Alert | When | Level |
| --- | --- | --- |
| Water leak | A `leak_sensors` entity is on | Critical |
| On battery | `ups_charging` is off | Critical |
| Unlocked | A lock is not locked at night, or while everyone is out | Warning |
| Lights on | A light is on at night, or while everyone is out | Warning |
| Bins out tonight | A collection is tomorrow and it is 17:00 or later | Info |

"Everyone is out" needs `persons` to be set. Light groups and
`ignored_lights` never raise the lights alert.

## Before installing: enable I2C

Home Assistant OS has no `raspi-config`, so turn the I2C bus on through the
boot partition. [`ha-os/boot`](https://github.com/TGTGamer/home-assistant-setup/tree/main/ha-os/boot)
in this repository has the files and `scripts/prepare-boot.sh` copies them onto
a freshly flashed card:

1. `config.txt` gains `dtparam=i2c1=on` and `dtparam=i2c_arm=on`.
2. `CONFIG/modules/rpi-i2c.conf` loads the `i2c-dev` and `i2c-bcm2708` modules.

On a system that is already running, the "HassOS I2C Configurator" community
app does the same job. Reboot the host twice afterwards.

## Install

1. Settings, Apps, App store, the three-dot menu, Repositories.
2. Add `https://github.com/TGTGamer/home-assistant-setup`.
3. Install **OLED Status**. The first install builds the image on the Pi,
   which takes a few minutes.
4. Fill in the options (below), then start the app.

## Options

Entity options take entity IDs, for example `lock.front_door`. Find them under
Settings, Devices and services, Entities. Leave an option empty to turn its
page or alert off.

| Option | Default | Meaning |
| --- | --- | --- |
| `i2c_port` | `1` | I2C bus. The app is given `/dev/i2c-1`; another bus also needs `devices` in `config.yaml` changed |
| `i2c_address` | `0x3C` | Display address; some use `0x3D` |
| `rotate` | `0` | 0 to 3, in quarter turns |
| `contrast` | `255` | Daytime brightness, 0 to 255 |
| `night_contrast` | `8` | Night brightness |
| `night_start`, `night_end` | `23:00`, `07:00` | Night window; may cross midnight |
| `screen_off_at_night` | `false` | Dark overnight unless there is an alert |
| `page_seconds` | `8` | Seconds per page |
| `refresh_seconds` | `5` | How often to read Home Assistant |
| `pages` | all | Pages to rotate, in order |
| `weather` | | `weather.*` entity |
| `climate` | | `climate.*` entity for the heating |
| `media_player` | | `media_player.*` entity |
| `ups_battery` | | Sensor giving the UPS battery percentage |
| `ups_charging` | | Entity that is `on` or `charging` on mains power |
| `persons` | | `person.*` entities |
| `locks` | | `lock.*` entities |
| `bins` | | Collection sensors (days until, a date, `today` or `tomorrow`, or a `daysTo` attribute) |
| `leak_sensors` | | `binary_sensor.*` moisture sensors |
| `ignored_lights` | | `light.*` entities that may stay on |

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| Log shows `No such file or directory: '/dev/i2c-1'` | I2C is off. Enable it (above) and reboot the host twice. |
| Log shows `I2C device not found on address` | Wrong address or loose cable. Try `0x3D`. |
| Screen stuck on "connecting..." | The app cannot read Home Assistant. Check the app log. |
| Text upside down | Set `rotate` to `2`. |

## Development

Everything runs off the Pi. From the repository root:

```sh
pnpm preview   # renders every page to previews/*.png from sample data
pnpm dev       # live data: needs HA_URL and HA_TOKEN, draws to previews/live.png
pnpm verify    # lint, types, tests, headers, licences
```
