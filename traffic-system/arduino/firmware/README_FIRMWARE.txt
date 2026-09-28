/*
  Placeholder for future Arduino Uno firmware (LDR R/Y/G sensing).

  Wire protocol (one line per sample), matching arduino/protocol.py:

    STATE:RED,ELAPSED:12.5,RED:45.0,YELLOW:3.0,GREEN:30.0

  Or JSON:

    {"state":"RED","elapsed_s":12.5,"durations":{"RED":45,"YELLOW":3,"GREEN":30}}

  Until hardware arrives, use Python MockTrafficLight / SignalWorker
  (scripts/smoke_step6.py) with ARDUINO_MOCK_ENABLED=true.
*/
