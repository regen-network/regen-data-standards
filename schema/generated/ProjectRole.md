

# Class: ProjectRole



URI: [rfs:ProjectRole](https://framework.regen.network/schema/ProjectRole)



```mermaid
erDiagram
ProjectRole {
    string name  
    string description  
    string url  
    ProjectRoleTypes type  
    string image  
}



```



<!-- no inheritance hierarchy -->


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [name](name.md) | 1 <br/> [String](String.md) | Name of the project | direct |
| [description](description.md) | 0..1 <br/> [String](String.md) | Optional description of the project | direct |
| [url](url.md) | 0..1 <br/> [String](String.md) |  | direct |
| [type](type.md) | 1 <br/> [ProjectRoleTypes](ProjectRoleTypes.md) |  | direct |
| [image](image.md) | 0..1 <br/> [String](String.md) |  | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [Project](Project.md) | [project_developer](project_developer.md) | range | [ProjectRole](ProjectRole.md) |






## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | rfs:ProjectRole |
| native | rfs:ProjectRole |







## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: ProjectRole
from_schema: https://framework.regen.network/schema/
slots:
- name
- description
- url
attributes:
  type:
    name: type
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:ProjectRoleType
    domain_of:
    - ProjectRole
    range: ProjectRoleTypes
    required: true
  image:
    name: image
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:image
    domain_of:
    - ProjectRole

```
</details>

### Induced

<details>
```yaml
name: ProjectRole
from_schema: https://framework.regen.network/schema/
attributes:
  type:
    name: type
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: rfs:ProjectRoleType
    alias: type
    owner: ProjectRole
    domain_of:
    - ProjectRole
    range: ProjectRoleTypes
    required: true
  image:
    name: image
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:image
    alias: image
    owner: ProjectRole
    domain_of:
    - ProjectRole
    range: string
  name:
    name: name
    description: Name of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:name
    alias: name
    owner: ProjectRole
    domain_of:
    - Project
    - ProjectRole
    - File
    range: string
    required: true
  description:
    name: description
    description: Optional description of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:description
    alias: description
    owner: ProjectRole
    domain_of:
    - Project
    - ProjectRole
    - File
    range: string
  url:
    name: url
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    alias: url
    owner: ProjectRole
    domain_of:
    - ProjectRole
    range: string

```
</details>