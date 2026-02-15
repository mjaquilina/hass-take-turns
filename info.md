# Take Turns

A Home Assistant integration that manages rotating lists of people, useful for tracking whose turn it is for chores, bedtime stories, choosing movies, etc.

## Features

- **State Persistence**: Remembers position across restarts
- **Services**: `next_turn` to advance, `set_person` to jump to someone specific
- **Dashboard Integration**: Easy to add buttons and entity cards
- **Automation Ready**: Perfect for scheduled rotations

## Quick Setup

1. Install via HACS
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Take Turns"
5. Fill in:
   - Entity ID (e.g., `bedtime_story`)
   - Friendly Name (e.g., "Bedtime Story Reader")
   - People (comma-separated: "Mom, Dad, Grandma")

## Example Uses

- Bedtime story reader rotation
- Dish duty assignment
- Movie night chooser
- Household chore rotation
- Turn-taking for games
- Pet feeding schedule

## Services

### `take_turns.next_turn`
Advance to the next person in the rotation.

### `take_turns.set_person`
Set a specific person as current.

## Documentation

Full documentation available in the [README](https://github.com/mjaquilina/hass-take-turns/blob/main/README.md).
