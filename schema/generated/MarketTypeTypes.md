# Enum: MarketTypeTypes




_The type of marketplace_



URI: [MarketTypeTypes](MarketTypeTypes.md)

## Permissible Values

| Value | Meaning | Description |
| --- | --- | --- |
| compliance | rfs:ComplianceMarket | a compliance market |
| voluntary | rfs:VoluntaryMarket | a voluntary market |




## Slots

| Name | Description |
| ---  | --- |
| [marketType](marketType.md) | The type of market for the associated credits |






## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/






## LinkML Source

<details>
```yaml
name: MarketTypeTypes
description: The type of marketplace
from_schema: https://framework.regen.network/schema/
rank: 1000
permissible_values:
  compliance:
    text: compliance
    description: a compliance market
    meaning: rfs:ComplianceMarket
  voluntary:
    text: voluntary
    description: a voluntary market
    meaning: rfs:VoluntaryMarket

```
</details>
