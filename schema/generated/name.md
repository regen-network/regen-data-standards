

# Slot: name


_Name of the project._





URI: [schema:name](http://schema.org/name)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ProjectRole](ProjectRole.md) |  |  no  |
| [File](File.md) |  |  no  |
| [Organization](Organization.md) |  |  no  |
| [Project](Project.md) |  |  no  |
| [AdministrativeArea](AdministrativeArea.md) |  |  no  |







## Properties

* Range: [String](String.md)

* Required: True





## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | schema:name |
| native | rfs:name |




## LinkML Source

<details>
```yaml
name: name
description: Name of the project.
from_schema: https://framework.regen.network/schema/
rank: 1000
slot_uri: schema:name
alias: name
domain_of:
- Project
- ProjectRole
- File
- Organization
- AdministrativeArea
range: string
required: true

```
</details>