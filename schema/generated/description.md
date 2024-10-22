

# Slot: description


_Optional description of the project._





URI: [schema:description](http://schema.org/description)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [TerrasosProjectInfo](TerrasosProjectInfo.md) |  |  no  |
| [File](File.md) |  |  no  |
| [Organization](Organization.md) |  |  no  |
| [ProjectInfo](ProjectInfo.md) |  |  no  |
| [ProjectRole](ProjectRole.md) |  |  no  |







## Properties

* Range: [String](String.md)

* Required: True





## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | schema:description |
| native | rfs:description |




## LinkML Source

<details>
```yaml
name: description
description: Optional description of the project.
from_schema: https://framework.regen.network/schema/
rank: 1000
slot_uri: schema:description
alias: description
domain_of:
- ProjectInfo
- ProjectRole
- Organization
- File
range: string
required: true

```
</details>