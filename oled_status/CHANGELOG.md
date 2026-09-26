# Changelog

## 0.1.1

- Fix start-up on Home Assistant OS. s6-overlay starts the app with a clean
  environment, which lost `PYTHONPATH` ("No module named oled_status") and
  would also have lost `SUPERVISOR_TOKEN`. The app now starts through
  `with-contenv`, as Home Assistant's own apps do, and the source path is
  registered with a `.pth` file.

## 0.1.0

- First release: clock, weather, people, locks, heating, bins, now playing,
  UPS, mood and starfield pages, with leak, power, lock, lights and bin-day
  alerts, night dimming and an optional dark screen overnight.
