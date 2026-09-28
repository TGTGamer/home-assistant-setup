# Roadmap

The old install mostly gathered apps into one place and linked them to voice
assistants. This time it should solve real day-to-day problems.

## 1. Operational

- [x] Home Assistant OS on the Pi 4 with the boot settings ([install](install.md))
- [x] SSH access with a key
- [x] deCONZ with Phoscon on the RaspBee II
- [x] Homeway: remote access, Google Assistant, MCP
- [x] UPS Plus integration and low-battery shutdown
- [x] OLED Status app (0.1.1 fixes start-up on HA OS)
- [ ] Core integrations: Hue, SmartThings, SimpliSafe, Hive, Nest, Sonos, phones
- [x] Add `core_freq=250` to the card's `config.txt` (done over SSH; see install guide)

## 2. Problems to solve

| Problem | Approach |
| --- | --- |
| Lights left on after bed or when out | Presence from the phones plus a bedtime signal (sleep sensors or a bedside button); alert, then switch off |
| Forgetting bin day | waste_collection_schedule for the council; phone notification and OLED alert the evening before |
| Heating | Hive with better_thermostat; schedule by who is home rather than fixed times |
| Front, back and gate locks | Choose smart locks first; that choice decides whether a Z-Wave stick is needed. keymaster for codes |

## 3. Later

- [ ] Wall panel: Pi 3 B+ with the 7 inch touch display in kiosk mode
- [ ] Z-Wave stick, if the chosen locks or devices need it
- [ ] An AI assistant (for example OpenClaw) on top of the Homeway MCP endpoint
- [ ] Case RGB fan as a status light, if its LEDs are addressable
