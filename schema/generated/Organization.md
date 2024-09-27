

# Class: Organization



URI: [rfs:Organization](https://framework.regen.network/schema/Organization)



```mermaid
erDiagram
Organization {
    string name  
    string url  
    boolean showOnProjectPage  
    string description  
    string image  
    string address  
}



```



<!-- no inheritance hierarchy -->


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [name](name.md) | 1 <br/> [String](String.md) | Name of the project | direct |
| [url](url.md) | 0..1 <br/> [String](String.md) |  | direct |
| [showOnProjectPage](showOnProjectPage.md) | 0..1 <br/> [Boolean](Boolean.md) | Whether to show this organization on the project page | direct |
| [description](description.md) | 0..1 <br/> [String](String.md) | Optional description of the project | direct |
| [image](image.md) | 0..1 <br/> [String](String.md) | an image | direct |
| [address](address.md) | 0..1 <br/> [String](String.md) | an address | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [ProjectPage](ProjectPage.md) | [environmentalAuthority](environmentalAuthority.md) | range | [Organization](Organization.md) |
| [ProjectPage](ProjectPage.md) | [projectOperator](projectOperator.md) | range | [Organization](Organization.md) |
| [ProjectPage](ProjectPage.md) | [projectMonitor](projectMonitor.md) | range | [Organization](Organization.md) |
| [ProjectPage](ProjectPage.md) | [projectOwner](projectOwner.md) | range | [Organization](Organization.md) |






## Identifier and Mapping Information







### Schema Source


* from schema: https://framework.regen.network/schema/




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | rfs:Organization |
| native | rfs:Organization |







## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: Organization
from_schema: https://framework.regen.network/schema/
slots:
- name
- url
- showOnProjectPage
- description
- image
- address
class_uri: rfs:Organization

```
</details>

### Induced

<details>
```yaml
name: Organization
from_schema: https://framework.regen.network/schema/
attributes:
  name:
    name: name
    description: Name of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:name
    alias: name
    owner: Organization
    domain_of:
    - Project
    - ProjectRole
    - File
    - Organization
    - AdministrativeArea
    range: string
    required: true
  url:
    name: url
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    alias: url
    owner: Organization
    domain_of:
    - ProjectRole
    - Organization
    - AdministrativeArea
    range: string
  showOnProjectPage:
    name: showOnProjectPage
    description: Whether to show this organization on the project page.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    alias: showOnProjectPage
    owner: Organization
    domain_of:
    - Organization
    range: boolean
  description:
    name: description
    description: Optional description of the project.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:description
    alias: description
    owner: Organization
    domain_of:
    - Project
    - ProjectRole
    - File
    - Organization
    range: string
  image:
    name: image
    description: an image.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:image
    alias: image
    owner: Organization
    domain_of:
    - ProjectRole
    - Organization
    range: string
  address:
    name: address
    description: an address.
    from_schema: https://framework.regen.network/schema/
    rank: 1000
    slot_uri: schema:address
    alias: address
    owner: Organization
    domain_of:
    - Organization
    range: string
class_uri: rfs:Organization

```
</details>