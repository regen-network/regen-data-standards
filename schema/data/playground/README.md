Process:

- Validate (maybe covered by Cory's PR?)

```shell
linkml-validate -s schema/src/schema.yaml --target-class C01ProjectInfo schema/data/playground/C01-001/C01ProjectInfo/C01-001.yaml 
```

Qs:

- What should the directory structure of `schema/data/playground` be?
- I assume we will have a script that validates and converts all yaml files in these directories.
- Important to consider how we identify the target class because for both the `linkml-validate` and `linkml-convert` commands we need to pass in a `--target-class` flag with value eg` `C01ProjectInfo`.

Some options might be:
- Create directories for each target class within `schema/data/playground/{class-name}`?
  - So `schema/data/playground/C01ProjectInfo/C01-001.yaml` + `schema/data/playground/CreditClassInfo/C01.yaml` ?
- But would it be nice to have a credit class directory with all credit class + project metadata files within that directory?
- `schema/data/playground/C01/C01ProjectInfo/C01-001.yaml + C01-002.yaml + etc`
- `schema/data/playground/C01/CreditClassInfo/C01.yaml`

- Convert to JSONLD

```shell
linkml-convert --input-format yaml --output-format json-ld --schema schema/src/schema.yaml schema/data/playground/C01-001/C01ProjectInfo/C01-001.yaml --output schema/data/playground/C01-001/C01ProjectInfo/C01-001.jsonld --target-class C01ProjectInfo
```

- Generate IRI 

```shell
regen q data generate-iri schema/data/playground/C01-001/C01ProjectInfo/C01-001.jsonld
```

- Send to triple-store. Use IRI as graph name?

```shell
curl -X PUT \
     -H "Content-Type: application/ld+json" \
     --data-binary "@$file" \
     "${FUSEKI_URL}/${DATASET_NAME}/data?graph=${IRI}"
```