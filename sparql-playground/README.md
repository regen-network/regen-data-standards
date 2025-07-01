# Sparql Playground

## Jena Fuseki

Run Fuseki using headless docker image: https://github.com/AtomGraph/fuseki-docker

Simples, using in-memory dataset:
```shell
docker run --rm -p 3030:3030 atomgraph/fuseki --mem /ds
```

## Utils

### `load-data.sh <directory>`

Loads all `*.jsonld` files from the `data` dir into the triple store using the SPARQL Graph Store API.
Optionally specify a sub-directory to load subset of files.

Each file's parent directory is the named graph it will load into - note that named graphs must be URIs! (special case for `default` named graph)

To load all files:

```shell
./load-data.sh
```

To only load files in `jsonld:demo` sub-directory into `jsonld:demo` graph:

```shell
./load-data.sh jsonld:demo
```

### `load-file.sh <file> <graph=default>`

Loads a single file in to the specified graph, or `default` graph if none specified.

To load example `person.jsonld` into the `default` graph` into the `default` graph:

```shell
./load-file.sh data/jsonld:demo/person.jsonld default
```

### `query.sh <query>`

Executes a SPARQL query referenced by name of the `*.sparql` file inside the `queries` directory.

To execute the `project.sparql` query:

```shell
./query.sh project
```