# Rhyme Display Configuration - PERMANENT SETTINGS

This document defines the **PERMANENT** display format for rhyme results. These settings are hardcoded and should NEVER be changed without explicit user approval.

## **METRICAL PATTERN DISPLAY FORMAT**

### **Required Format:**
```
Word: syllables * stress-pattern, metrical-foot
```

### **Examples:**
- `Double: 2 * 1-0, Trochee`
- `Table: 2 * 1-0, Trochee`
- `Muscle: 2 * 1-0, Trochee`
- `Justice: 2 * 1-0, Trochee`

### **Components:**
1. **Word**: The rhyme word
2. **Syllables**: Number of syllables (e.g., `2`)
3. **Stress Pattern**: Uses hyphens between stress marks (e.g., `1-0`, `0-1-0`)
4. **Metrical Foot**: Italicized name (e.g., `*Trochee*`, `*Iamb*`)

## **SOURCE COLOR CODING**

### **Color Scheme:**
- **🔵 DM**: Blue circle = Datamuse results
- **🟢 CMU**: Green circle = CMU/our model results

### **Implementation:**
- Added to every rhyme result display
- Helps distinguish between external API and local model results
- Critical for development and debugging

## **COMPLETE DISPLAY FORMAT**

### **Full Format:**
```
{emoji} **{word}** ({popularity_bar}) {source_indicator}{source_text}: {syllables} * {stress_pattern}, {metrical_foot}
```

### **Example:**
```
⭐ **trouble** (████████░░) 🟢CMU: 2 * 1-0, Trochee
≈ **muscle** (█████░░░░░) 🔵DM: 2 * 1-0, Trochee
```

## **APPLICATION SCOPE**

This format applies to **ALL** rhyme result types:
- ✅ Perfect Rhymes (Popular & Technical)
- ✅ Slant Rhymes (Near-Perfect & Assonance)  
- ✅ Colloquial Phrases

## **PERMANENT STATUS**

- **Status**: HARDCODED
- **Change Policy**: Requires explicit user approval
- **Purpose**: Consistent, professional rhyme analysis display
- **User Request**: "Save that somewhere where it will be hardcoded and not disappear"

## **Technical Implementation**

### **File Locations:**
- `app.py`: `format_rhyme_item()` function
- `RHYME_DISPLAY_CONFIG.md`: This permanent configuration

### **Key Functions:**
- `get_stress_pattern_from_db()`: Retrieves metrical data
- `format_rhyme_item()`: Applies display format
- Source detection: `datamuse_verified` and `source` fields

---

**⚠️ IMPORTANT**: These display settings are PERMANENT and should not be modified without explicit user consent. The user specifically requested this format to be "hardcoded and not disappear."


