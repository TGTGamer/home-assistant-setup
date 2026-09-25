# Previous setup (2022 to 2025)

What the old install had, recorded from its backup so the rebuild can pick
what to keep. Account names, addresses and device identifiers are left out.

## Platform

- Phoscon's Raspbian 10 (Buster) gateway image, 32-bit, with deCONZ 2.19.1
  serving Phoscon on port 80. Its `deconz-wifi` service ran a Wi-Fi setup
  hotspot, which is why the Pi broadcast its own network.
- Home Assistant 2023.5 in Docker (compose), with Portainer, Node-RED and a
  web config editor alongside. All four have Home Assistant OS equivalents.
- The OLED ran `luma.examples`' `sys_info.py`; `rpi_ws281x` had been tried for
  RGB LEDs.
- The history database was repeatedly flagged corrupt in December 2024, a
  common sign of a wearing SD card, so the old card is not reused.
- No Zigbee devices were ever paired to the RaspBee; Zigbee devices were on the
  Hue bridge and SmartThings instead.

## Integrations, with device counts

| Integration | Devices | Note |
| --- | --- | --- |
| Philips Hue | 25 | Hue bridge; keep |
| SmartThings | 35 | |
| SimpliSafe | 19 | Alarm |
| Google Cast | 14 | |
| Hive | 8 | Heating |
| Nest | 3 | |
| Mobile app | 3 | Two phones and a watch |
| Sonos, Samsung TV, Android TV Remote, Xbox, DLNA | 1 each | |
| Spotify, Withings (two people), Speedtest, UptimeRobot, CO2 Signal, Met.no, GitHub, IFTTT | | Account-based |
| Home Assistant Cloud | | Google Assistant linking; subscription had lapsed |

## HACS custom components

keymaster, better_thermostat, scheduler, waste_collection_schedule,
auto_areas, presence_simulation, rental_control (no longer needed),
anniversaries, browser_mod, ui_lovelace_minimalist, auto_backup, fontawesome,
steam_wishlist, overwolfstatus.

## Automations

Seven: turn off the house, a partner out of bed, the partner back in bed
(Withings sleep sensor), a water sensor alert, automatic backups, an IFTTT
bridge, and one unnamed draft.
