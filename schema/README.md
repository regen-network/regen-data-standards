# Schema

[LinkML](https://linkml.io/) semantic schemas for Regen Network framework.

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

- Datasets are provided inside `schema/data/playground/{Credit-Class}/{LinkML-Class}/*.yaml` files
- Validate and generate RDF data. This creates `.ttl` and `.jsonld` files for each dataset.
    ```shell
    make gen-rdf
    ```
- Add data to graph. This adds all `.ttl` files to the graph. Override the `GRAPH_STORE_URL` env var:
  ```shell
  export GRAPH_STORE_URL=http://localhost:7878/store
  make update-graph
  ```