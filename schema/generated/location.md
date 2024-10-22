

# Slot: location


_The location of the project._





URI: [schema:location](http://schema.org/location)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TerrasosProjectInfo](TerrasosProjectInfo.md) |  |  no  |
| [ProjectInfo](ProjectInfo.md) |  |  no  |
| [File](File.md) |  |  no  |







## Properties

* Range: [Location](Location.md)

* Required: True





## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | schema:location |
| native | rfs:location |




## LinkML Source

<details>
```yaml
name: location
description: The location of the project.
from_schema: https://framework.regen.network/schema/
rank: 1000
slot_uri: schema:location
alias: location
domain_of:
- ProjectInfo
- File
range: Location
required: true
inlined: true

```
</details>