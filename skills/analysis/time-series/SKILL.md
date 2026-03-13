---
name: time-series
description: |
  Patterns for temporal analysis of Montréal data: trends, year-over-year
  comparisons, seasonal patterns, and anomaly detection across datasets
  with varying date formats and update frequencies.
  / Stratégies d'analyse temporelle : tendances, comparaisons annuelles,
  patrons saisonniers et détection d'anomalies.
triggers:
  - trend, over time, year, month, season, growth, decline, compare years
  - tendance, au fil du temps, année, mois, saison, croissance, comparer
---

# Time Series Analysis / Analyse temporelle

## Date Fields by Dataset / Champs de date par jeu de données

| Dataset | Date Field | Format | Granularity |
|---------|-----------|--------|-------------|
| Crime | `DATE` | `2024-01-15` | Day |
| Permits | `date_emission` | `2024-01-15` | Day |
| 311 | `DDS_DATE_CREATION` | `2024-01-15 08:30:00` | Minute |
| Fire | `CREATION_DATE_TIME` | `2024-01-15T08:30:00` | Minute |
| Collisions | `DT_ACCDN` | `2023-01-15` | Day |
| Trees (survey) | `Date_Releve` | `2018-06-26T00:00:00` | Day |
| Trees (planted) | `Date_Plantation` | `2004-06-10T00:00:00` | Day |
| Budget | Year embedded in data | Various | Year |

---

## Pattern 1: Monthly Trend / Tendance mensuelle

Most useful for 311, crime, permits. Uses SQL `SUBSTRING` to extract year-month.

```sql
-- Monthly crime trend
SELECT SUBSTRING("DATE", 1, 7) as month,
       COUNT(*) as incidents
FROM "c6f482bf-bf0f-4960-8b2f-9ca22b2d4e88"
WHERE "DATE" >= '2023-01-01'
GROUP BY SUBSTRING("DATE", 1, 7)
ORDER BY month
```

```sql
-- Monthly permit issuance by type
SELECT SUBSTRING("date_emission", 1, 7) as month,
       "description_type_demande" as type,
       COUNT(*) as count
FROM "5232a72d-2355-4e8c-8e1c-a3a0b4e1b867"
WHERE "date_emission" >= '2024-01-01'
GROUP BY month, type
ORDER BY month
```

---

## Pattern 2: Year-over-Year / Comparaison annuelle

```sql
-- Crime by year
SELECT SUBSTRING("DATE", 1, 4) as year, COUNT(*) as total
FROM "c6f482bf-bf0f-4960-8b2f-9ca22b2d4e88"
GROUP BY year ORDER BY year

-- 311 by year and nature
SELECT SUBSTRING("DDS_DATE_CREATION", 1, 4) as year,
       "NATURE" as type,
       COUNT(*) as count
FROM "2cfa0e06-9be7-46f1-9b3d-fee3f9174754"
WHERE "NATURE" IN ('Propreté', 'Chaussée et trottoir', 'Éclairage de rue')
GROUP BY year, type ORDER BY year
```

---

## Pattern 3: Day-of-Week / Jour de la semaine

CKAN SQL doesn't have a native `DAYOFWEEK` function. Use client-side:

```python
from datetime import datetime
from collections import Counter

crimes = ckan_sql('''
    SELECT "DATE", "CATEGORIE" FROM "c6f482bf-bf0f-4960-8b2f-9ca22b2d4e88"
    WHERE "DATE" >= '2025-01-01' LIMIT 32000
''')

day_counts = Counter()
for c in crimes:
    dt = datetime.strptime(c['DATE'][:10], '%Y-%m-%d')
    day_counts[dt.strftime('%A')] += 1

# Result: which day of week has most crime
```

---

## Pattern 4: Seasonal Patterns / Patrons saisonniers

Montréal has extreme seasonality. Key patterns:

| What | Winter (Dec-Mar) | Spring (Apr-May) | Summer (Jun-Aug) | Fall (Sep-Nov) |
|------|---------|--------|--------|------|
| 311 requests | Snow, ice, heating | Potholes, flooding | Noise, waste, parks | Leaves, prep |
| Crime | Lower | Rising | Peak | Declining |
| Permits | Low | Surge | Steady | Declining |
| Fire | Heating fires | Lower | BBQ, fireworks | Lower |
| BIXI | Inactive | Opens April | Peak | Closes November |
| Collisions | Ice conditions | Normal | Construction zones | Back to school |

```sql
-- Seasonal crime pattern (extract month)
SELECT SUBSTRING("DATE", 6, 2) as month, COUNT(*) as incidents
FROM "c6f482bf-bf0f-4960-8b2f-9ca22b2d4e88"
WHERE "DATE" >= '2024-01-01'
GROUP BY month ORDER BY month
```

---

## Pattern 5: Growth Rate / Taux de croissance

```python
# Year-over-year growth for permits
permits_by_year = ckan_sql('''
    SELECT SUBSTRING("date_emission", 1, 4) as year, COUNT(*) as count
    FROM "5232a72d-2355-4e8c-8e1c-a3a0b4e1b867"
    WHERE "date_emission" >= '2020-01-01'
    GROUP BY year ORDER BY year
''')

for i in range(1, len(permits_by_year)):
    prev = int(permits_by_year[i-1]['count'])
    curr = int(permits_by_year[i]['count'])
    growth = ((curr - prev) / prev) * 100
    print(f"{permits_by_year[i]['year']}: {curr:,} ({growth:+.1f}%)")
```

---

## Pattern 6: Moving Average / Moyenne mobile

For smoothing noisy daily data (especially 311 or crime):

```python
from collections import deque

def moving_average(daily_counts, window=7):
    """Compute N-day moving average."""
    buffer = deque(maxlen=window)
    result = []
    for date, count in sorted(daily_counts.items()):
        buffer.append(count)
        result.append((date, sum(buffer) / len(buffer)))
    return result
```

---

## Pattern 7: Before/After Analysis / Analyse avant/après

Useful for measuring impact of events (new bike lane, policy change, etc.):

```python
# 311 requests in Le Plateau before and after a date
before = ckan_sql('''
    SELECT COUNT(*) as n FROM "2cfa0e06-9be7-46f1-9b3d-fee3f9174754"
    WHERE "ARRONDISSEMENT" LIKE '%Plateau%'
    AND "DDS_DATE_CREATION" BETWEEN '2024-06-01' AND '2024-08-31'
''')

after = ckan_sql('''
    SELECT COUNT(*) as n FROM "2cfa0e06-9be7-46f1-9b3d-fee3f9174754"
    WHERE "ARRONDISSEMENT" LIKE '%Plateau%'
    AND "DDS_DATE_CREATION" BETWEEN '2025-06-01' AND '2025-08-31'
''')

change_pct = ((int(after[0]['n']) - int(before[0]['n'])) / int(before[0]['n'])) * 100
```

---

## Gotchas / Pièges

1. **Date formats vary.** Some use `T` separator, others space, others just date. Parse carefully.
2. **Incomplete years.** Current year data is partial — don't compare 2026 totals to full-year 2025.
3. **SUBSTRING is your friend.** CKAN SQL supports `SUBSTRING(field, start, length)` for date extraction.
4. **No date functions.** No `YEAR()`, `MONTH()`, `DAYOFWEEK()` — use SUBSTRING or client-side.
5. **Timezone.** All timestamps are Eastern Time (Montréal), not UTC.
6. **32K limit applies.** Daily data for 3+ years may exceed 32K rows. Aggregate server-side.
7. **Seasonal bias.** Always compare same months across years to avoid seasonal distortion.
8. **COVID gap.** 2020-2021 data has anomalies across almost every dataset.

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | N/A — agent-side analysis patterns |
| **Applies to** | All time-stamped Montréal datasets |
| **Last verified** | March 2026 |

## Related Skills / Compétences connexes

- `cross-dataset-joins` — Combining temporal data across datasets
- `data-freshness` — Understanding update frequencies
- `visualization` — Presenting time series as charts
