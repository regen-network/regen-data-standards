

# Class: ManagementArea



URI: [rfs:ManagementArea](https://framework.regen.network/schema/ManagementArea)



```mermaid
erDiagram
ManagementArea {
    ActivityTypesList activity  
}
QuantityValue {
    float numericValue  
    string unit  
}

ManagementArea ||--|o QuantityValue : "extent"

```



<!-- no inheritance hierarchy -->


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [activity](activity.md) | * <br/> [ActivityTypes](ActivityTypes.md) | the activity | direct |
| [extent](extent.md) | 0..1 <br/> [QuantityValue](QuantityValue.md) | the extent | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [Project](Project.md) | [managementAreas](managementAreas.md) | range | [ManagementArea](ManagementArea.md) |






## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | rfs:ManagementArea |
| native | rfs:ManagementArea |







## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: ManagementArea
from_schema: https://framework.regen.network/schema/
slots:
- activity
- extent
class_uri: rfs:ManagementArea

```
</details>

### Induced

<details>
```yaml
name: ManagementArea
from_schema: https://framework.regen.network/schema/
attributes:
  activity:
    name: activity
    description: the activity.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:activity
    alias: activity
    owner: ManagementArea
    domain_of:
    - Project
    - ManagementArea
    range: ActivityTypes
    multivalued: true
  extent:
    name: extent
    description: the extent.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: dcterms:extent
    alias: extent
    owner: ManagementArea
    domain_of:
    - ManagementArea
    range: QuantityValue
class_uri: rfs:ManagementArea

```
</details>