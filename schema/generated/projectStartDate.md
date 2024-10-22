

# Slot: projectStartDate


_The start date of the project._





URI: [xsd:date](http://www.w3.org/2001/XMLSchema#date)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TerrasosProjectInfo](TerrasosProjectInfo.md) |  |  no  |
| [ProjectInfo](ProjectInfo.md) |  |  no  |







## Properties

* Range: [String](String.md)





## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | xsd:date |
| native | rfs:projectStartDate |




## LinkML Source

<details>
```yaml
name: projectStartDate
description: The start date of the project.
from_schema: https://framework.regen.network/schema/
rank: 1000
slot_uri: xsd:date
alias: projectStartDate
domain_of:
- ProjectInfo
range: string

```
</details>