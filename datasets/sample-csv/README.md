# Sample product catalogue

Synthetic reference dataset used to demonstrate and test the pipeline. Not for sale.

| Field | Type | Required | Description |
|---|---|---|---|
| sku | string | yes | Stock keeping unit |
| name | string | yes | Product name |
| category | string | no | Product category |
| price | number | yes | Unit price |
| currency | string | yes | ISO 4217 code |
| in_stock | boolean | no | Available now |
| released_on | date | no | Release date (YYYY-MM-DD) |

- Coverage: 5 synthetic products; rows failing the schema are quarantined, not published.
- Update frequency: static.
- Source & license: synthetic, CC0-1.0.
- Known limitations: toy data only.
