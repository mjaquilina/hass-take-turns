# Take Turns - Home Assistant Custom Integration

A Home Assistant integration that manages rotating lists of people, useful for tracking whose turn it is for chores, bedtime stories, choosing movies, etc.

## Installation

### Method 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu (top right) → "Custom repositories"
4. Add repository URL: `https://github.com/mjaquilina/hass-take-turns`
5. Select category: "Integration"
6. Click "Add"
7. Click "Download" on the Take Turns card
8. Restart Home Assistant

### Method 2: Manual Installation

1. Copy the `custom_components/take_turns` folder to your Home Assistant `config/custom_components/` directory.

2. Restart Home Assistant.

3. The integration is now ready to use!

## Configuration

You can configure Take Turns in two ways:

### Option 1: UI Configuration (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Take Turns"
4. Fill in the form:
   - **Entity ID**: The identifier for the sensor (e.g., `bedtime_story` creates `sensor.bedtime_story`)
   - **Friendly Name**: Display name (e.g., "Bedtime Story Reader")
   - **People**: Comma-separated list of names (e.g., "Mom, Dad, Grandma")
5. Click **Submit**

To edit an existing entity:
1. Go to **Settings** → **Devices & Services** → **Take Turns**
2. Click **Configure** on the entity you want to edit
3. Update the name or people list
4. Click **Submit**

To delete an entity:
1. Go to **Settings** → **Devices & Services** → **Take Turns**
2. Click the three dots menu on the entity
3. Select **Delete**

### Option 2: YAML Configuration

Add to your `configuration.yaml`:

```yaml
take_turns:
  bedtime_story:
    name: "Bedtime Story Reader"
    people:
      - Alice
      - Bob
      - Charlie
  
  dish_duty:
    name: "Dish Duty"
    people:
      - Mike
      - Sarah
      - Jenny
```

Restart Home Assistant to load the configuration.

**Note**: You can mix both methods. YAML and UI configurations work together seamlessly.

## Usage

### Entities Created

For each configured item, a sensor entity is created:
- Entity ID: `sensor.<your_key>` (e.g., `sensor.bedtime_story`, `sensor.dish_duty`)
- State: Current person's name
- Attributes:
  - `people`: Full list of people
  - `current_index`: Current position in the list (0-based)
  - `friendly_name`: Display name

### Services

#### `take_turns.next_turn`

Advances to the next person in the list (wraps around to the beginning after the last person).

**Parameters:**
- `entity_id` (required): The entity to advance (e.g., `bedtime_story`)

**Example Service Call:**
```yaml
service: take_turns.next_turn
data:
  entity_id: bedtime_story
```

#### `take_turns.set_person`

Sets the current person to a specific individual from the list.

**Parameters:**
- `entity_id` (required): The entity to modify (e.g., `bedtime_story`)
- `person` (required): The name of the person to set as current (must match exactly)

**Example Service Call:**
```yaml
service: take_turns.set_person
data:
  entity_id: bedtime_story
  person: Charlie
```

### Automation Example

Advance automatically every night at 8 PM:

```yaml
automation:
  - alias: "Rotate Bedtime Story Reader"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: take_turns.next_turn
        data:
          entity_id: bedtime_story
```

### Dashboard Button Example

Add a button to your dashboard to manually advance:

```yaml
type: button
name: Next Person
icon: mdi:rotate-right
tap_action:
  action: call-service
  service: take_turns.next_turn
  data:
    entity_id: bedtime_story
```

### Display Current Person

Use an entity card to show who's currently up:

```yaml
type: entity
entity: sensor.bedtime_story
name: Tonight's Story Reader
```

Or use a markdown card for more detail:

```yaml
type: markdown
content: >
  **Bedtime Story:** {{ states('sensor.bedtime_story') }}
  
  **Dish Duty:** {{ states('sensor.dish_duty') }}
```

## Configuration Options

Each take_turns entity supports:

- `people` (required): List of names to rotate through
- `name` (optional): Friendly display name (defaults to formatted entity_id)

## Notes

- The integration persists state to disk automatically. After a Home Assistant restart, it resumes from the last person.
- State is stored in `.storage/take_turns.state.json` in your Home Assistant config directory.
- The list wraps around automatically (after the last person, it goes back to the first).
- If you change the people list in `configuration.yaml` and the saved index is out of bounds, it resets to the first person.

