

# Class: TerrasosProjectInfo



URI: [rfs:TerrasosProjectInfo](https://framework.regen.network/schema/TerrasosProjectInfo)



```mermaid
erDiagram
TerrasosProjectInfo {
    float ecologicalConnectivityIndex  
    float socialCulturalIndex  
    ConservationStatusTypes conservationStatus  
    string projectDuration  
    MarketTypeTypesList marketType  
    stringList bioregion  
    stringList biomeType  
    string watershed  
    string subWatershed  
    string name  
    string description  
    ActivityTypesList projectActivities  
    EnvironmentTypeTypesList environmentType  
    string projectStartDate  
    string projectEndDate  
    string creditClassVersion  
}
ProjectRole {
    string name  
    string url  
    string image  
    string description  
    ProjectRoleTypes type  
}
QuantityValue {
    float numericValue  
    string unit  
}
Location {
    string type  
    string placeName  
    string id  
    floatList bbox  
    string text  
    floatList center  
    float relevance  
    string placeType  
}
Any {

}
Geometry {
    string type  
    floatList coordinates  
}
Organization {
    string name  
    string url  
    boolean showOnProjectPage  
    string image  
    string description  
}
ManagementArea {
    ActivityTypesList projectActivity  
}
AdministrativeArea {
    string name  
    string url  
}

TerrasosProjectInfo ||--|o AdministrativeArea : "administrativeArea"
TerrasosProjectInfo ||--}o ManagementArea : "managementAreas"
TerrasosProjectInfo ||--|o ProjectRole : "projectOperator"
TerrasosProjectInfo ||--|o ProjectRole : "projectOwner"
TerrasosProjectInfo ||--}o Organization : "environmentalAuthority"
TerrasosProjectInfo ||--|| Location : "location"
TerrasosProjectInfo ||--|o QuantityValue : "projectSize"
TerrasosProjectInfo ||--|o ProjectRole : "projectDeveloper"
TerrasosProjectInfo ||--|o ProjectRole : "projectMonitor"
TerrasosProjectInfo ||--|o ProjectRole : "projectVerifier"
Location ||--|| Geometry : "geometry"
Location ||--|o Any : "context"
Location ||--|o Any : "properties"
ManagementArea ||--|o QuantityValue : "extent"

```




## Inheritance
* [ProjectInfo](ProjectInfo.md)
    * **TerrasosProjectInfo**



## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [ecologicalConnectivityIndex](ecologicalConnectivityIndex.md) | 0..1 <br/> [Float](Float.md) | The ecological connectivity index of the project | direct |
| [socialCulturalIndex](socialCulturalIndex.md) | 0..1 <br/> [Float](Float.md) | The social cultural index of the project | direct |
| [administrativeArea](administrativeArea.md) | 0..1 <br/> [AdministrativeArea](AdministrativeArea.md) | The administrative area associated with the project | direct |
| [managementAreas](managementAreas.md) | * <br/> [ManagementArea](ManagementArea.md) | The management areas associated with the project | direct |
| [conservationStatus](conservationStatus.md) | 0..1 <br/> [ConservationStatusTypes](ConservationStatusTypes.md) | The conservation status of the project | direct |
| [projectDuration](projectDuration.md) | 0..1 <br/> [String](String.md) | The duration of the project | direct |
| [projectOperator](projectOperator.md) | 0..1 <br/> [ProjectRole](ProjectRole.md) | The organization responsible for operating the project | direct |
| [projectOwner](projectOwner.md) | 0..1 <br/> [ProjectRole](ProjectRole.md) | The organization responsible for owning the project | direct |
| [marketType](marketType.md) | * <br/> [MarketTypeTypes](MarketTypeTypes.md) | The type of market for the associated credits | direct |
| [environmentalAuthority](environmentalAuthority.md) | * <br/> [Organization](Organization.md) | The environmental authority associated with the project | direct |
| [bioregion](bioregion.md) | * <br/> [String](String.md) | The bioregion associated with the project | direct |
| [biomeType](biomeType.md) | * <br/> [String](String.md) | The type of biome associated with the project | direct |
| [watershed](watershed.md) | 0..1 <br/> [String](String.md) | The watershed associated with the project | direct |
| [subWatershed](subWatershed.md) | 0..1 <br/> [String](String.md) | The sub-watershed associated with the project | direct |
| [name](name.md) | 1 <br/> [String](String.md) | Name of the project | [ProjectInfo](ProjectInfo.md) |
| [location](location.md) | 1 <br/> [Location](Location.md) | The location of the project | [ProjectInfo](ProjectInfo.md) |
| [description](description.md) | 1 <br/> [String](String.md) | Optional description of the project | [ProjectInfo](ProjectInfo.md) |
| [projectActivities](projectActivities.md) | * <br/> [ActivityTypes](ActivityTypes.md) | the activity | [ProjectInfo](ProjectInfo.md) |
| [projectSize](projectSize.md) | 0..1 <br/> [QuantityValue](QuantityValue.md) |  | [ProjectInfo](ProjectInfo.md) |
| [projectDeveloper](projectDeveloper.md) | 0..1 <br/> [ProjectRole](ProjectRole.md) | The organization responsible for owning the project | [ProjectInfo](ProjectInfo.md) |
| [environmentType](environmentType.md) | * <br/> [EnvironmentTypeTypes](EnvironmentTypeTypes.md) | The environment type of the project | [ProjectInfo](ProjectInfo.md) |
| [projectMonitor](projectMonitor.md) | 0..1 <br/> [ProjectRole](ProjectRole.md) | The organization responsible for monitoring the project | [ProjectInfo](ProjectInfo.md) |
| [projectVerifier](projectVerifier.md) | 0..1 <br/> [ProjectRole](ProjectRole.md) | The organization responsible for owning the project | [ProjectInfo](ProjectInfo.md) |
| [projectStartDate](projectStartDate.md) | 0..1 <br/> [String](String.md) | The start date of the project | [ProjectInfo](ProjectInfo.md) |
| [projectEndDate](projectEndDate.md) | 0..1 <br/> [String](String.md) | The end date of the project | [ProjectInfo](ProjectInfo.md) |
| [creditClassVersion](creditClassVersion.md) | 0..1 <br/> [String](String.md) | The version of the credit class used for the project | [ProjectInfo](ProjectInfo.md) |









## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | rfs:TerrasosProjectInfo |
| native | rfs:TerrasosProjectInfo |







## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: TerrasosProjectInfo
from_schema: https://framework.regen.network/schema/
is_a: ProjectInfo
slots:
- ecologicalConnectivityIndex
- socialCulturalIndex
- administrativeArea
- managementAreas
- conservationStatus
- projectDuration
- projectOperator
- projectOwner
- marketType
- environmentalAuthority
- bioregion
- biomeType
- watershed
- subWatershed
class_uri: rfs:TerrasosProjectInfo

```
</details>

### Induced

<details>
```yaml
name: TerrasosProjectInfo
from_schema: https://framework.regen.network/schema/
is_a: ProjectInfo
attributes:
  ecologicalConnectivityIndex:
    name: ecologicalConnectivityIndex
    description: The ecological connectivity index of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:ecologicalConnectivityIndex
    alias: ecologicalConnectivityIndex
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: float
  socialCulturalIndex:
    name: socialCulturalIndex
    description: The social cultural index of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:socialCulturalIndex
    alias: socialCulturalIndex
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: float
  administrativeArea:
    name: administrativeArea
    description: The administrative area associated with the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    alias: administrativeArea
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: AdministrativeArea
  managementAreas:
    name: managementAreas
    description: The management areas associated with the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:managementAreas
    alias: managementAreas
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: ManagementArea
    multivalued: true
    inlined: true
  conservationStatus:
    name: conservationStatus
    description: The conservation status of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:conservationStatus
    alias: conservationStatus
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: ConservationStatusTypes
  projectDuration:
    name: projectDuration
    description: The duration of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:projectDuration
    alias: projectDuration
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: string
  projectOperator:
    name: projectOperator
    description: The organization responsible for operating the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:projectOperator
    alias: projectOperator
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: ProjectRole
  projectOwner:
    name: projectOwner
    description: The organization responsible for owning the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:projectOwner
    alias: projectOwner
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: ProjectRole
  marketType:
    name: marketType
    description: The type of market for the associated credits.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:marketType
    alias: marketType
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: MarketTypeTypes
    multivalued: true
  environmentalAuthority:
    name: environmentalAuthority
    description: The environmental authority associated with the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:environmentalAuthority
    alias: environmentalAuthority
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: Organization
    multivalued: true
    inlined: true
    inlined_as_list: true
  bioregion:
    name: bioregion
    description: The bioregion associated with the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:bioregion
    alias: bioregion
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: string
    multivalued: true
  biomeType:
    name: biomeType
    description: The type of biome associated with the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:biomeType
    alias: biomeType
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: string
    multivalued: true
  watershed:
    name: watershed
    description: The watershed associated with the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:watershed
    alias: watershed
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: string
  subWatershed:
    name: subWatershed
    description: The sub-watershed associated with the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:subWatershed
    alias: subWatershed
    owner: TerrasosProjectInfo
    domain_of:
    - TerrasosProjectInfo
    range: string
  name:
    name: name
    description: Name of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:name
    alias: name
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    - ProjectRole
    - Organization
    - File
    - AdministrativeArea
    range: string
    required: true
  location:
    name: location
    description: The location of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:location
    alias: location
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    - File
    range: Location
    required: true
    inlined: true
  description:
    name: description
    description: Optional description of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:description
    alias: description
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    - ProjectRole
    - Organization
    - File
    range: string
    required: true
  projectActivities:
    name: projectActivities
    description: the activity.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:projectActivities
    alias: projectActivities
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: ActivityTypes
    multivalued: true
  projectSize:
    name: projectSize
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    alias: projectSize
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: QuantityValue
    inlined: false
  projectDeveloper:
    name: projectDeveloper
    description: The organization responsible for owning the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:projectDeveloper
    alias: projectDeveloper
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: ProjectRole
  environmentType:
    name: environmentType
    description: The environment type of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:environmentType
    alias: environmentType
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: EnvironmentTypeTypes
    multivalued: true
  projectMonitor:
    name: projectMonitor
    description: The organization responsible for monitoring the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:projectMonitor
    alias: projectMonitor
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: ProjectRole
  projectVerifier:
    name: projectVerifier
    description: The organization responsible for owning the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:projectVerifier
    alias: projectVerifier
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: ProjectRole
  projectStartDate:
    name: projectStartDate
    description: The start date of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: xsd:date
    alias: projectStartDate
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: string
  projectEndDate:
    name: projectEndDate
    description: The end date of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: xsd:date
    alias: projectEndDate
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: string
  creditClassVersion:
    name: creditClassVersion
    description: The version of the credit class used for the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:creditClassVersion
    alias: creditClassVersion
    owner: TerrasosProjectInfo
    domain_of:
    - ProjectInfo
    range: string
class_uri: rfs:TerrasosProjectInfo

```
</details>