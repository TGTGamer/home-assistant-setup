# Changelog

## 0.1.1

- Fix start-up on Home Assistant OS: the app failed with "No module named
  oled_status" because s6-overlay drops `PYTHONPATH`. The source path is now
  registered with a `.pth` file.

## 0.1.0

- First release: clock, weather, people, locks, heating, bins, now playing,
  UPS, mood and starfield pages, with leak, power, lock, lights and bin-day
  alerts, night dimming and an optional dark screen overnight.
