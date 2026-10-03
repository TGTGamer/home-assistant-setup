# Changelog

## 0.2.0

- New `leaks` page listing each `leak_sensors` entity as wet or dry, on by
  default after `bins`.
- New `dino` page: the mood face as a dinosaur, bouncing and blinking when all
  is well, sweating and shaking while alerts are active. List it instead of
  `mood`, or alongside it.
- New `dino_run` page: the dinosaur runs across a scrolling desert and jumps
  the cacti.

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
