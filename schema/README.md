# Schema

[LinkML](https://linkml.io/) semantic schemas for Regen Network framework.

These schemas define the structure and semantics for credit class and project metadata in the Regen Network ecosystem. They provide a standardized way to describe:

- **Credit Class Information**: Metadata for carbon and biodiversity credit classes, including protocols, methodologies, eligible activities, and environment types
- **Project Information**: Geospatial and descriptive data for projects enrolled in a given credit class
- **Impact Tracking**: Primary impacts and co-benefits associated with projects
- **Taxonomies**: Controlled vocabularies for activities, environment types, and impact types

The schemas are designed to be converted to RDF/JSON-LD formats for semantic web integration and SPARQL querying.

> **Note**: Current on-chain datasets may not fully reflect this schema. The schemas in this repository (and the playground folder) represent the latest up-to-date versions of all Regen Network datasets in a format consistent with current Regen Data Standards.

## Requirements

[Install LinkML](https://linkml.io/linkml/intro/install.html) to use the helper and generator commands for interacting with LinkML schemas and data.

## Structure

- LinkML schemas are created in `schema/src`.
- Create separate schema files for each logical schema class and `import` into the root `schemas.yaml` file.
- Generated markdown from schemas:
  ```shell
  make gen-doc
  ```
- Generate linkml enums for taxonomy terms:
  ```shell
  make gen-taxonomy
  ```

## Playground

Datasets are provided inside `schema/data/playground/{Credit-Class}/{LinkML-Class}-*.yaml` files. All datasets are managed in github as YAML files as this is more lightweight and easier to manage (as the standardized source for LinkML datasets) than storing JSON-LD or TTL files in version control.

There is a designated make task (`gen-rdf`) for validating and generating RDF data in formats besides YAML. This creates `.ttl` and `.jsonld` files for each dataset. To run the script, use the following command:

```shell
make gen-rdf
```

## SPARQL Integration

If you are running a SPARQL endpoint, you can use the following command to push datasets via a GRAPH_STORE API to update datasets to a live SPARQL store. This adds all `.ttl` files to the graph. Override the `GRAPH_STORE_URL` env var:

```shell
export GRAPH_STORE_URL=http://localhost:7878/store
make update-graph
```
