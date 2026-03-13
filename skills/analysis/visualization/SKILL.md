---
name: visualization
description: |
  Patterns for presenting Montréal open data as charts, maps, and tables
  suitable for agent-generated output: HTML/SVG inline charts, text-based
  tables, map links, and data formatted for external tools.
  / Stratégies de visualisation : graphiques HTML/SVG, tableaux texte,
  liens cartographiques, et formats pour outils externes.
triggers:
  - chart, graph, map, visualize, plot, show me, display, dashboard, table
  - graphique, carte, visualiser, afficher, tableau de bord
---

# Visualization / Visualisation

## Output Formats / Formats de sortie

An AI agent typically can't render a browser, but it CAN:

1. **Generate HTML/SVG** that the user opens
2. **Format text tables** in the chat
3. **Provide map links** (Google Maps, OpenStreetMap)
4. **Export CSV** for the user's tools (Excel, Tableau, etc.)
5. **Generate React/JSX** components for interactive dashboards

---

## Pattern 1: Text Table / Tableau texte

Best for: Small result sets (< 20 rows) shown directly in chat.

```python
def format_table(records, columns, headers=None):
    """Format records as aligned text table."""
    if not headers:
        headers = columns
    widths = [max(len(h), max(len(str(r.get(c, ''))) for r in records)) for c, h in zip(columns, headers)]

    header_line = '  '.join(h.ljust(w) for h, w in zip(headers, widths))
    separator = '  '.join('─' * w for w in widths)
    rows = []
    for r in records:
        rows.append('  '.join(str(r.get(c, '')).ljust(w) for c, w in zip(columns, widths)))

    return f"{header_line}\n{separator}\n" + "\n".join(rows)

# Example: Top 10 boroughs by tree count
trees = ckan_sql('''
    SELECT "ARROND_NOM" as borough, COUNT(*) as trees
    FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
    GROUP BY "ARROND_NOM" ORDER BY trees DESC LIMIT 10
''')
print(format_table(trees, ['borough', 'trees'], ['Borough', 'Trees']))
```

---

## Pattern 2: Map Link / Lien cartographique

Best for: Single locations or small sets of points.

```python
def osm_link(lat, lon, zoom=16):
    """OpenStreetMap link centered on a point."""
    return f"https://www.openstreetmap.org/#map={zoom}/{lat}/{lon}"

def google_maps_link(lat, lon):
    """Google Maps link."""
    return f"https://www.google.com/maps?q={lat},{lon}"

# For a specific tree or permit location
print(f"📍 See on map: {osm_link(45.5231, -73.5744)}")
```

For multiple points, use the CKAN map view:
```
https://donnees.montreal.ca/dataset/DATASET_SLUG/resource/RESOURCE_UUID
```

---

## Pattern 3: Inline SVG Bar Chart / Graphique à barres SVG

Best for: Agents that can output HTML (Cowork, Claude artifacts).

```python
def svg_bar_chart(data, label_key, value_key, title="", width=600, height=400):
    """Generate inline SVG bar chart."""
    max_val = max(int(d[value_key]) for d in data)
    bar_height = max(15, (height - 80) // len(data))

    bars = []
    for i, d in enumerate(data):
        val = int(d[value_key])
        bar_w = (val / max_val) * (width - 250)
        y = 50 + i * (bar_height + 4)
        label = str(d[label_key])[:25]
        bars.append(f'''
            <text x="145" y="{y + bar_height//2 + 4}" text-anchor="end" font-size="12">{label}</text>
            <rect x="150" y="{y}" width="{bar_w}" height="{bar_height}" fill="#2563eb" rx="3"/>
            <text x="{155 + bar_w}" y="{y + bar_height//2 + 4}" font-size="11" fill="#666">{val:,}</text>
        ''')

    total_h = 60 + len(data) * (bar_height + 4)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" style="font-family: Inter, sans-serif;">
        <text x="{width//2}" y="30" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>
        {''.join(bars)}
    </svg>'''
```

---

## Pattern 4: CSV Export / Export CSV

Best for: Users who want to work with data in their own tools.

```python
import csv
import io

def to_csv(records, filename=None):
    """Convert API records to CSV string."""
    if not records:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[k for k in records[0].keys() if k != '_id'])
    writer.writeheader()
    for r in records:
        writer.writerow({k: v for k, v in r.items() if k != '_id'})

    text = output.getvalue()
    if filename:
        with open(filename, 'w', encoding='utf-8-sig') as f:
            f.write(text)
    return text
```

---

## Pattern 5: React Component / Composant React

Best for: Interactive dashboards in Claude artifacts or web apps.

```jsx
// Borough comparison dashboard
import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function BoroughDashboard() {
  const [data, setData] = useState([]);

  useEffect(() => {
    // Agent: replace this URL with actual CKAN SQL endpoint
    fetch('https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=...')
      .then(r => r.json())
      .then(d => setData(d.result.records));
  }, []);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data} layout="vertical">
        <XAxis type="number" />
        <YAxis type="category" dataKey="borough" width={180} />
        <Tooltip />
        <Bar dataKey="count" fill="#2563eb" />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

---

## Pattern 6: Choropleth Hint / Indication choroplèthe

For borough-level data, the agent can describe what a map WOULD look like and link to the portal's built-in map:

```
📊 Borough comparison (trees per km²):
  🟢 Dark green: Rosemont (1,247/km²), Plateau (1,182/km²)
  🟡 Medium: Villeray (934/km²), Sud-Ouest (876/km²)
  🔴 Low: Saint-Laurent (312/km²), Anjou (287/km²)

🗺️ See the full interactive map: https://donnees.montreal.ca/dataset/arbres
```

---

## Color Palette for Charts / Palette de couleurs

Use Montréal's civic palette for on-brand visualizations:

| Use | Color | Hex |
|-----|-------|-----|
| Primary | Montréal Blue | `#003B6F` |
| Accent | Civic Red | `#D62828` |
| Positive | Green | `#2D6A4F` |
| Warning | Orange | `#E76F51` |
| Neutral | Grey | `#6C757D` |
| Background | Light | `#F8F9FA` |

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | N/A — agent-side visualization patterns |
| **Applies to** | All Montréal datasets |
| **Last verified** | March 2026 |

## Related Skills / Compétences connexes

- `cross-dataset-joins` — Data to visualize
- `time-series` — Temporal charts
- `borough-context` — Geographic grouping for maps
