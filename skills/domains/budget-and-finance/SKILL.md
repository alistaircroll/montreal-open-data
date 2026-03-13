---
name: budget-and-finance
description: |
  Access Montréal's operating budget, contracts, subsidies, procurement, tax rates,
  real estate transactions, and participatory budget results. Analyze spending,
  track supplier activity, and explore financial accountability.
  / Accéder au budget de fonctionnement de Montréal, aux contrats, subventions,
  approvisionnement, tarifs fiscaux, transactions immobilières et résultats du budget
  participatif. Analyser les dépenses, suivre les fournisseurs et examiner la reddition
  de comptes financière.
triggers:
  - budget, spending, contract, supplier, grant, subsidy, tax, finance, procurement
  - budget, dépenses, contrat, fournisseur, subvention, taxe, finances, approvisionnement
---

# Budget & Finance / Budget et finances

## Available Datasets / Jeux de données disponibles

| Dataset Slug | Title | Format | DataStore? | Content |
|--------------|-------|--------|------------|---------|
| `budget` | Operating Budget | CSV | ✓ Yes | Annual budget by department, line item, amount |
| `contrats-octroyes-par-les-fonctionnaires-ville-centrale` | Contracts by City Officials | CSV | ✓ Yes | Contracts awarded by central city staff |
| `contrats-conseil-municipal-et-conseil-d-agglomeration` | Council Contracts | CSV | ✓ Yes | Municipal & agglomeration council contracts |
| `contrats-comite-executif` | Executive Committee Contracts | CSV | ✓ Yes | Contracts authorized by exec committee |
| `contrats-conseils-d-arrondissement` | Borough Council Contracts | CSV | ✓ Yes | Contracts from borough councils (16 arrondissements) |
| `subventions-conseil-de-ville-et-d-agglomeration` | Council Grants | CSV | ✓ Yes | Grants from municipal & agglomeration councils |
| `subventions-du-comite-executif` | Executive Committee Grants | CSV | ✓ Yes | Grants authorized by executive committee |
| `liste-des-fournisseurs` | Supplier List | CSV | ✓ Yes | All active suppliers; used in procurement |
| `depenses-des-elus-autorisees-par-le-comite-executif` | Elected Officials' Expenses | CSV | ✓ Yes | Approved expenses for city councilors |
| `reddition-comptes-financiere` | Financial Accountability | CSV | ✓ Yes | Annual financial statements summary |
| `taux-de-taxation-et-tarification` | Tax Rates & Tarification | CSV | ✓ Yes | Property tax rates, service fees |
| `liste-des-transactions-immobilieres` | Real Estate Transactions | CSV | ✓ Yes | City-owned property sales, purchases |
| `budget-participatif-montreal` | Participatory Budget Results | CSV | ✓ Yes | Winning projects from citizen voting |
| `programme-triennal-d-immobilisation-fiches-de-projets-et-programmes` | Capital Program | CSV | ✓ Yes | 3-year capital projects & programs |

---

## IMPORTANT: Contracts & Subsidies API (Non-CKAN)

**The `contrats-et-subventions-api` is a SEPARATE API, not accessible via CKAN DataStore.**

This API provides a **unified interface** for contracts and subsidies:
- **Base URL:** `https://api.donneesquebec.ca/api/3/action/` (Données Québec, not CKAN)
- **NOT a CKAN package** — different authentication & response format
- Do NOT query it via CKAN's `datastore_search_sql`
- Use standard REST GET requests instead

**Recommendation:** For most analyses, use the CKAN datasets above (they are CSV-based, easier). Only use the API if you need **real-time** contract/subsidy lookups.

---

## 1. Budget / Budget de fonctionnement

### Dataset Overview

```bash
# Find DataStore resource ID
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=budget' | \
  python3 -c "
import json, sys
for r in json.load(sys.stdin)['result']['resources']:
    if r.get('datastore_active'):
        print(f'DataStore ID: {r[\"id\"]}')
"
```

**Typical fields:**
- Department, division, program code
- Line item description (personnel, supplies, capital, etc.)
- Budget amount (CAD), actual spending, variance
- Fiscal year (starts Jan 1)
- Department code / classification

**Common SQL queries:**

```sql
-- Budget by department
SELECT "DEPARTMENT", SUM(CAST("BUDGET_AMOUNT" AS FLOAT)) as total_budget
FROM "RESOURCE_UUID"
GROUP BY "DEPARTMENT"
ORDER BY total_budget DESC

-- Current year spending vs. budget
SELECT "LINE_ITEM", "BUDGET_AMOUNT", "ACTUAL_SPENDING",
       (CAST("ACTUAL_SPENDING" AS FLOAT) / CAST("BUDGET_AMOUNT" AS FLOAT) * 100) as pct_used
FROM "RESOURCE_UUID"
WHERE "FISCAL_YEAR" = 2026
ORDER BY pct_used DESC
```

---

## 2. Contracts / Contrats

### Key Point: Multiple Authorization Levels

**Montreal has FOUR contract datasets based on authorization authority:**

1. **City officials (central)** — `contrats-octroyes-par-les-fonctionnaires-ville-centrale`
2. **City Council + Agglomeration Council** — `contrats-conseil-municipal-et-conseil-d-agglomeration`
3. **Executive Committee** — `contrats-comite-executif`
4. **Borough Councils (16 arrondissements)** — `contrats-conseils-d-arrondissement`

**All use the same column structure**, but represent different governance levels. When analyzing contracts, you may need to combine these datasets.

### Common Fields

- Contractor name & address
- Contract amount (CAD)
- Award date, start date, end date
- Work description / subject
- Responsible department / borough

### Contract Query Examples

```sql
-- Find all contracts for a specific supplier
SELECT "CONTRACTOR_NAME", "AMOUNT", "START_DATE", "END_DATE", "DESCRIPTION"
FROM "RESOURCE_UUID"
WHERE LOWER("CONTRACTOR_NAME") LIKE '%contractor-name%'
ORDER BY "START_DATE" DESC

-- Largest contracts in current year
SELECT "CONTRACTOR_NAME", "AMOUNT", "DESCRIPTION", "AWARD_DATE"
FROM "RESOURCE_UUID"
WHERE CAST("AMOUNT" AS FLOAT) > 500000
ORDER BY "AMOUNT" DESC

-- Contract count by borough (from borough council contracts)
SELECT "BOROUGH", COUNT(*) as contract_count, SUM(CAST("AMOUNT" AS FLOAT)) as total_value
FROM "RESOURCE_UUID"
GROUP BY "BOROUGH"
ORDER BY total_value DESC
```

### CDN-NDG Exception

**Côte-des-Neiges–Notre-Dame-de-Grâce (CDN-NDG) maintains its own contract archive** outside CKAN.
- Not all CDN-NDG contracts may appear in the borough-level dataset
- Check the borough's local website for complete history
- This is a known gap in unified data

---

## 3. Subsidies & Grants / Subventions

### Two Datasets by Source

| Dataset | Authorization | Content |
|---------|---------------|---------|
| `subventions-conseil-de-ville-et-d-agglomeration` | Municipal & agglomeration councils | Grants approved by elected bodies |
| `subventions-du-comite-executif` | Executive committee | Grants approved by exec committee |

### Common Fields

- Recipient organization name
- Grant amount (CAD)
- Program / purpose code
- Approval date, payment date
- Duration (one-time, recurring)

### Subsidy Queries

```sql
-- Grants to non-profits in a specific sector
SELECT "RECIPIENT", "AMOUNT", "PURPOSE", "APPROVAL_DATE"
FROM "RESOURCE_UUID"
WHERE "PURPOSE" LIKE '%health%' OR "PURPOSE" LIKE '%sante%'
ORDER BY "AMOUNT" DESC

-- Sum of grants by recipient over time
SELECT "RECIPIENT", COUNT(*) as grant_count, SUM(CAST("AMOUNT" AS FLOAT)) as total_received
FROM "RESOURCE_UUID"
WHERE CAST("APPROVAL_DATE" AS DATE) > '2023-01-01'
GROUP BY "RECIPIENT"
HAVING SUM(CAST("AMOUNT" AS FLOAT)) > 100000
ORDER BY total_received DESC
```

---

## 4. Supplier List / Liste des fournisseurs

### Dataset Overview

**Dataset:** `liste-des-fournisseurs`

Contains all active suppliers registered with the City for procurement.

### Fields

- Supplier legal name, trade name
- Supplier ID / registration number
- Category (supplies, services, construction, etc.)
- Contact info (optional)
- Status (active, inactive, suspended)
- Business classification

### Supplier Analysis

```sql
-- Active suppliers by category
SELECT "CATEGORY", COUNT(*) as supplier_count
FROM "RESOURCE_UUID"
WHERE "STATUS" = 'active'
GROUP BY "CATEGORY"
ORDER BY supplier_count DESC

-- Find a specific supplier
SELECT * FROM "RESOURCE_UUID"
WHERE LOWER("SUPPLIER_NAME") LIKE '%business-name%'

-- Suppliers not used in recent contracts
-- (Requires joining with contract dataset)
```

---

## 5. Elected Officials' Expenses / Dépenses des élus

### Dataset Overview

**Dataset:** `depenses-des-elus-autorisees-par-le-comite-executif`

Approved expenses for elected officials (councilors, mayor, borough mayors).

### Common Fields

- Official name, title, borough/ward
- Expense category (travel, meals, office supplies, etc.)
- Amount (CAD)
- Date approved, date incurred
- Business / vendor name

### Query Examples

```sql
-- Expenses by councilor
SELECT "OFFICIAL_NAME", SUM(CAST("AMOUNT" AS FLOAT)) as total_expenses
FROM "RESOURCE_UUID"
WHERE CAST("DATE_APPROVED" AS DATE) BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY "OFFICIAL_NAME"
ORDER BY total_expenses DESC

-- Travel expenses over threshold
SELECT "OFFICIAL_NAME", "VENDOR", "AMOUNT", "CATEGORY", "DATE_INCURRED"
FROM "RESOURCE_UUID"
WHERE "CATEGORY" = 'travel' AND CAST("AMOUNT" AS FLOAT) > 5000
ORDER BY "AMOUNT" DESC
```

---

## 6. Tax Rates & Tarification / Taux de taxation

### Dataset Overview

**Dataset:** `taux-de-taxation-et-tarification`

Property tax rates, service fees, and user charges.

### Content

- Property class (residential, commercial, industrial)
- Tax rate per $100 of assessed value
- Municipal tax, agglomeration tax, school tax (if applicable)
- Service fees (water, sewer, waste, parking, etc.)
- Effective date, changes year-over-year

### Common Queries

```sql
-- Current residential tax rate by borough
SELECT "BOROUGH", "PROPERTY_CLASS", "MILL_RATE"
FROM "RESOURCE_UUID"
WHERE "PROPERTY_CLASS" = 'residential'
AND "EFFECTIVE_DATE" = (SELECT MAX("EFFECTIVE_DATE") FROM "RESOURCE_UUID")

-- Historical tax rate changes
SELECT "BOROUGH", "PROPERTY_CLASS", "MILL_RATE", "EFFECTIVE_DATE"
FROM "RESOURCE_UUID"
WHERE "PROPERTY_CLASS" IN ('residential', 'commercial')
ORDER BY "EFFECTIVE_DATE" DESC
```

---

## 7. Real Estate Transactions / Transactions immobilières

### Dataset Overview

**Dataset:** `liste-des-transactions-immobilieres`

City-owned property acquisitions, sales, and disposals.

### Fields

- Property address, lot number
- Type of transaction (purchase, sale, gift, expropriation)
- Amount (CAD, or N/A if gift/donation)
- Date of transaction
- Purpose / use
- Department or bureau responsible

### Analysis Examples

```sql
-- Property acquisitions by year
SELECT CAST(EXTRACT(YEAR FROM "TRANSACTION_DATE") AS INT) as year,
       COUNT(*) as acquisitions,
       SUM(CAST("AMOUNT" AS FLOAT)) as total_spent
FROM "RESOURCE_UUID"
WHERE "TRANSACTION_TYPE" = 'purchase'
GROUP BY year
ORDER BY year DESC

-- Largest property sales (revenue to city)
SELECT "ADDRESS", "AMOUNT", "PURPOSE", "TRANSACTION_DATE"
FROM "RESOURCE_UUID"
WHERE "TRANSACTION_TYPE" = 'sale'
ORDER BY CAST("AMOUNT" AS FLOAT) DESC
LIMIT 20
```

---

## 8. Financial Accountability / Reddition de comptes financière

### Dataset Overview

**Dataset:** `reddition-comptes-financiere`

Annual financial statements and audited accounts.

### Content

- Assets, liabilities, equity summaries
- Revenue by source (taxes, fees, grants, transfers)
- Expenditures by department
- Surplus/deficit for the fiscal year
- Audit status and date

Used for compliance and public transparency reporting.

---

## 9. Participatory Budget / Budget participatif

### Dataset Overview

**Dataset:** `budget-participatif-montreal`

Results of citizen-voted participatory budget projects.

### Fields

- Project title, description
- Proponent / idea author
- Winning year / round
- Approved budget amount
- Location / borough
- Status (approved, in progress, completed)

### Queries

```sql
-- Winning projects by borough
SELECT "BOROUGH", COUNT(*) as approved_projects,
       SUM(CAST("BUDGET_AMOUNT" AS FLOAT)) as total_allocated
FROM "RESOURCE_UUID"
GROUP BY "BOROUGH"
ORDER BY total_allocated DESC

-- Completed vs. in-progress projects
SELECT "STATUS", COUNT(*) as count, SUM(CAST("BUDGET_AMOUNT" AS FLOAT)) as total
FROM "RESOURCE_UUID"
GROUP BY "STATUS"
```

---

## 10. Capital Program / Programme triennal d'immobilisation

### Dataset Overview

**Dataset:** `programme-triennal-d-immobilisation-fiches-de-projets-et-programmes`

3-year capital projects and infrastructure programs.

### Fields

- Project name, description
- Department responsible
- Total estimated cost (CAD)
- Start year, end year
- Budget allocation by year (Year 1, Year 2, Year 3)
- Category (roads, water, recreation, etc.)

### Common Queries

```sql
-- Capital projects by department & category
SELECT "DEPARTMENT", "CATEGORY", COUNT(*) as project_count,
       SUM(CAST("TOTAL_COST" AS FLOAT)) as total_investment
FROM "RESOURCE_UUID"
GROUP BY "DEPARTMENT", "CATEGORY"
ORDER BY total_investment DESC

-- High-cost infrastructure projects
SELECT "PROJECT_NAME", "TOTAL_COST", "START_YEAR", "END_YEAR", "DESCRIPTION"
FROM "RESOURCE_UUID"
WHERE CAST("TOTAL_COST" AS FLOAT) > 10000000
ORDER BY "TOTAL_COST" DESC
```

---

## Common Questions / Questions fréquentes

| Question | Dataset(s) | Approach |
|----------|-----------|----------|
| "How much does the city spend on [department]?" | `budget` | Filter by department, sum budget amounts |
| "Who are the city's biggest contractors?" | `contrats-*` | Group by contractor name, sum amounts across datasets |
| "What tax rate applies to my property?" | `taux-de-taxation-et-tarification` | Filter by property class & borough, get current mill rate |
| "Was a subsidy given to [organization]?" | `subventions-*` | Search recipient name across both subsidy datasets |
| "List all suppliers in [category]" | `liste-des-fournisseurs` | Filter by supplier category, status = active |
| "What capital projects are planned?" | `programme-triennal-d-immobilisation-fiches-de-projets-et-programmes` | Browse by category, year |
| "How much real estate did the city buy/sell?" | `liste-des-transactions-immobilieres` | Sum by transaction type, filter by year |
| "What projects won participatory budget?" | `budget-participatif-montreal` | Filter by year, borough, status |

---

## Gotchas & Edge Cases / Pièges et cas limites

1. **Multiple contract datasets.** Montreal breaks contracts into 4 datasets by authorization level. Combining all is normal. CDN-NDG has its own archive outside CKAN.

2. **Currency is CAD.** All amounts are in Canadian dollars. Never assume USD or assume conversion.

3. **Fiscal year ≠ calendar year.** Montreal's fiscal year runs **Jan 1 – Dec 31** (same as calendar). Some reports may reference prior years.

4. **Tax rates change annually.** Always check the latest `EFFECTIVE_DATE` in tarification data. Rates from 2024 may not apply to current queries.

5. **Field names vary slightly.** Column names in the actual DataStore may differ from examples here. Always check the dataset's `datastore_info` endpoint first.

6. **Supplier list is active only.** Inactive/historical suppliers may not appear. Use contract datasets to find historical vendor activity.

7. **Assessed value ≠ market value.** The property assessment data (used for tax rates) is reassessed every 3 years and may differ from real sale prices.

8. **Contracts can have amendments.** Some contract datasets may list amendments separately. Check if there are related records.

9. **Approved ≠ paid.** Grant approval date and payment date can differ significantly. Track both for cash flow analysis.

10. **Real estate transactions may be gifts.** Transaction type includes gifts, expropriation, etc. — not always sales. Check `TRANSACTION_TYPE` before assuming monetary value.

---

## Provenance / Provenance

| Source | Publisher | Gov Level | License | Contact |
|--------|-----------|-----------|---------|---------|
| Budget | Ville de Montréal (Service de la gestion financière) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Contracts (all 4 datasets) | Ville de Montréal (Service de l'approvisionnement) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Subsidies (all 2 datasets) | Ville de Montréal (Conseil municipal & Comité exécutif) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Supplier List | Ville de Montréal (Service de l'approvisionnement) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Elected Officials' Expenses | Ville de Montréal (Comité exécutif) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Financial Accountability | Ville de Montréal (Bureau du vérificateur général) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Tax Rates | Ville de Montréal (Direction de l'évaluation foncière) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Real Estate Transactions | Ville de Montréal (Service des domaines) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Participatory Budget | Ville de Montréal (Bureau du budget participatif) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Capital Program | Ville de Montréal (Service des immobilisations) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Contracts & Subsidies API | Données Québec (Portal) | Provincial (multi-agency) | CC BY 4.0 | Via donneesquebec.ca |

---

## Related Skills / Compétences connexes

- `query-dataset` — DataStore SQL query patterns & best practices
- `borough-context` — Borough names, codes, and boundaries
- `discover-datasets` — Find budget/finance datasets on CKAN
- `permits-and-planning` — Property assessment, land use (complement to real estate data)
- `temporal-queries` — Filtering by fiscal year, date ranges
