# Schema

[LinkML](https://linkml.io/) semantic schemas for Regen Network framework.

## Requirements

[Install LinkML](https://linkml.io/linkml/intro/install.html) to use the helper and generator commands for interacting with LinkML schemas and data.

## Structure

- LinkML schemas are created in `schema/src`.
- Create separate schema files for each logical schema class and `import` into the root `schemas.yaml` file.
- Generated markdown from schemas:
    ```shell
    gen-doc schema/src/schemas.yml --directory schema/generated --diagram-type er_diagram
    ```