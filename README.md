# PS Audio Power Plant for Home Assistant

A local-polling custom integration for PS Audio PerfectWave / DirectStream Power Plant regenerators. It was written for the P20 and tested on firmware 0.01.25 (web 1.22.00).

It talks to the unit over HTTP on TCP port 80, using the `commands.cgi` status and control commands from PS Audio's PowerPlay programming manual. You add the integration by entering the unit's IP address. Nothing in this repository is specific to one installation.

## Entities

- **Power** switch: on, or off for standby.
- **Five zone switches:** Zone A (outlets 1–4), B (5–8), C (9–12), D (high-current, 13–14) and E (high-current, 15–16). A zone is on if any of its outlets reports on. Commands go to the zone's first outlet (`ZP=<first>,ON|OFF`); the unit switches the whole zone, not a single outlet.
- **Sixteen read-only outlet status** binary sensors (Outlet 1 through Outlet 16). Rename them in Home Assistant to match what is plugged in. Each has its zone letter as an attribute.
- **Measurements and settings:** input/output voltage, input/output THD, output current, output power, frequency, two temperatures; diagnostic DC offset, voltage setting, MultiWave strength, regulation mode, waveform, and the unit's reported watts (disabled by default). Diagnostic binary sensors cover MOV status (disabled by default) and lockout.

Output power is calculated as output volts × amps. The unit's own watts field is unreliable on the P20, so it is not used for the power sensor.

## Install with HACS

This is not in the default HACS catalog. Add it as a custom repository:

1. In Home Assistant, open **HACS**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Repository URL: `https://github.com/johncarey70/ha-psaudio-powerplant`
4. Category: **Integration**.
5. Add the repository, then find **PS Audio Power Plant** in HACS and download it.
6. Restart Home Assistant.
7. Go to **Settings → Devices & services → Add integration**, choose **PS Audio PowerPlant**, and enter the unit's IP address.

Home Assistant must be able to reach the unit on TCP port 80. Minimum Home Assistant version is 2024.7.0.

Manual install is also possible: copy `custom_components/psaudio_powerplant` into `/config/custom_components/` and restart.

## Care with the unit

The Power Plant's network side can freeze under heavy use; recovery is a power cycle at the back of the unit.

- This integration polls once every 60 seconds by default (minimum 30 seconds, changeable under Configure).
- It makes one request per poll, never runs two requests at once, and does not retry on failure.
- Avoid leaving the unit's web page open, and avoid other frequent HTTP polling of the same unit.

Front-panel dim and MultiWave cannot be changed over the network.

## License

MIT, copyright John Carey 2026.
