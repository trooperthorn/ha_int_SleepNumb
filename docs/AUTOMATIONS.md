# Blueprints

Ready-to-import automation blueprints that put local presence and sleep state to
work across the rest of your Home Assistant setup. Import via **Settings →
Automations & scenes → Blueprints → Import**, using the blueprint's GitHub URL.

| Blueprint | What it does |
|-----------|--------------|
| `close_windows_before_rain.yaml` | When everyone is in bed and rain is forecast, remind you to close the windows and optionally close covers. |
| `goodnight_scene.yaml` | When the last person gets in bed (after a set time), run your goodnight routine — lock up, lights off, arm the alarm. |
| `solar_night_mode.yaml` | Switch your solar/battery system to overnight behaviour when the bed is occupied, and restore it in the morning. |
| `severe_weather_wake.yaml` | Escalate a severe-weather warning with a critical notification (and optional lights) only while someone is asleep. |
| `climate_sleep_setback.yaml` | Ease the thermostat back once you're in bed and restore comfort when you get up. |

Each blueprint takes the SleepNumber **In bed** binary sensors as inputs, plus
whatever targets it acts on (a notify service, covers, a thermostat, or your own
action blocks). The energy- and weather-facing ones are deliberately left open so
they slot onto whatever solar, weather, or climate integrations you already run.

## Tips

- The "everyone in bed" blueprints treat presence as an **AND** across all the
  sensors you pass; the goodnight one fires on the transition that completes the
  set.
- For `severe_weather_wake`, point the warning input at a binary sensor from your
  weather provider (many expose per-alert sensors, or use a template that turns
  on for the alert types you care about).
- `solar_night_mode` and `climate_sleep_setback` use the action selector, so you
  can drop in any service calls your equipment needs without editing the YAML.
