# World macro indicators by country and year (2000-2025)

Long-format panel (one row = economy × indicator × year) of core World Development Indicators,
ready to load into any SQL/BI tool. Regional and income-group aggregates are excluded; empty
observations are dropped.

| Field | Type | Required | Description |
|---|---|---|---|
| country_code | string | yes | ISO 3166-1 alpha-3 code (World Bank) |
| country_name | string | yes | World Bank economy name |
| indicator_code | string | yes | WDI indicator code |
| indicator_name | string | yes | WDI indicator name incl. unit |
| year | integer | yes | Observation year |
| value | number | yes | Observed value, unit per `indicator_name` |

Indicators: `NY.GDP.MKTP.CD` GDP (current US$), `NY.GDP.PCAP.CD` GDP per capita (current US$),
`NY.GDP.MKTP.KD.ZG` GDP growth (annual %), `SP.POP.TOTL` population, `FP.CPI.TOTL.ZG` inflation,
consumer prices (annual %).

- Coverage: all World Bank economies (~217), years 2000-2025 where available.
- Update frequency: on demand; every refresh with changed data is released as a new version.
- Source & license: The World Bank, World Development Indicators, via the Indicators API v2,
  CC BY 4.0. This product is also CC BY 4.0 and must keep that attribution.
- Known limitations: values are as published by the World Bank (no imputation); latest years are
  incomplete and may be revised in later releases.
