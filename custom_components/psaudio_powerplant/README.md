# PS Audio PowerPlant for Home Assistant

Local-polling integration for PS Audio PowerPlants (written for the P20,
firmware 1.25). It reads the unit's `commands.cgi?command=RA` status dump
once per poll and can switch the unit between on and standby.

## Entities

- **Power** switch: on, or off = standby.
- Five zone switches: Zone A (outlets 1-4), B (5-8), C (9-12), D (HC, 13-14)
  and E (HC, 15-16). A zone is on if any of its outlets reports on; commands
  go to the zone's first outlet (`ZP=<first>,ON|OFF`), and the unit switches
  the whole zone.
- Sensors: input/output voltage, input/output THD, output current, output
  power (output volts x amps, because the unit's own watts field is
  unreliable on the P20), frequency, two temperatures; diagnostic DC offset
  (unitless), voltage setting, MultiWave strength, regulation mode, waveform,
  and the unit's reported watts (disabled by default).
- Sixteen read-only outlet status binary sensors, "Outlet 1" to "Outlet 16"
  (rename them in Home Assistant after what is plugged in); each carries its
  zone letter as an attribute.
- Diagnostic binary sensors: MOV status (disabled by default), unit lockout.

## Install

1. Copy `psaudio_powerplant` into `/config/custom_components/`.
2. Restart Home Assistant.
3. Settings > Devices & services > Add integration > PS Audio PowerPlant,
   then enter the unit's IP address.

Home Assistant must be able to reach the unit on TCP port 80.

## Care with the unit

The PowerPlant's network side is known to freeze under heavy use (recovery
is a power cycle at the back). This integration makes one request per poll,
polls every 60 s by default (minimum 30 s, change under Configure), never
runs two requests at once, and does not retry on failure. Avoid also leaving
the unit's web page open in a browser.

Commands (`UP=ON`, `UP=OFF`, `ZP=<n>,ON|OFF`) come from PS Audio's PowerPlay
programming manual.
