# Metrical Pattern Display - Project Standard

This document defines the standard format for displaying metrical pattern information in rhyme results.

## Display Format

Each rhyme result displays metrical information in the following format:

```
{emoji} **{word}** ({popularity_bar}) ({syllables}syl, {stress_pattern} *{metrical_foot}*)
```

### Examples:
- `⭐ **table** (████████░░) (2syl, 1-0 *trochee*)`
- `✓ **muscle** (█████░░░░░) (2syl, 1-0 *trochee*)`
- `≈ **justice** (██████░░░░) (2syl, 1-0 *trochee*)`

## Components

### 1. Stress Pattern Format
- **Format**: Uses hyphens between stress marks
- **Values**: Only `1` (stressed), `0` (unstressed), and hyphens
- **Examples**: `1-0`, `0-1-0`, `1-0-1`

### 2. Metrical Foot Names
- **Format**: Italicized in asterisks
- **Common feet**:
  - `trochee` (1-0): stressed-unstressed
  - `iamb` (0-1): unstressed-stressed  
  - `dactyl` (1-0-0): stressed-unstressed-unstressed
  - `anapest` (0-0-1): unstressed-unstressed-stressed
  - `spondee` (1-1): stressed-stressed

### 3. Data Sources
- **Stress patterns**: From CMU Pronouncing Dictionary
- **Metrical foot mapping**: Using `METRICAL_FEET` dictionary in `app.py`
- **Syllable counts**: From CMU database

## Implementation

This format is implemented in the `format_rhyme_item()` function in `app.py`:

```python
# Get metrical pattern name
_, metrical_foot, _ = get_stress_pattern_from_db(word)
metrical_display = f" *{metrical_foot}*" if metrical_foot else ""

# Format stress pattern (ensure 1-0 format)
if stress:
    stress_clean = stress.replace('2', '1').replace(' ', '-')
    stress_display = stress_clean
else:
    stress_display = 'N/A'

# Add metrical info: syllables, stress pattern, metrical foot
result += f" ({syls}syl, {stress_display}{metrical_display})"
```

## User Request History

The user has repeatedly requested this metrical pattern display format. This document ensures the format is preserved and can be referenced without repeated requests.

**Key Requirements from User:**
1. Stress patterns in "1-0" format (not "10")
2. Metrical pattern names (iamb, trochee, etc.) displayed
3. Syllable counts included
4. All rhyme results show this information consistently


