gen-taxonomy:
	python3 scripts/populateSemanticEnums.py

lint:
	linkml-lint src/ -a

gen-doc:
	gen-doc src/schema.yaml --directory generated --diagram-type er_diagram -v

gen-rdf:
	scripts/gen-rdf.sh

# Published schema artifacts (versions/<version>/, versions/manifest.json),
# generated from src/schema.yaml and its imports for the version it declares.
gen-context:
	python3 scripts/schema-artifacts.py generate context

gen-json-schema:
	python3 scripts/schema-artifacts.py generate json-schema

gen-shacl:
	python3 scripts/schema-artifacts.py generate shacl

# The examples are built with the generated context, then copied into the
# version's bundle with the manifest entry.
gen-schema-artifacts:
	python3 scripts/schema-artifacts.py generate
	python3 scripts/claim-examples.py generate
	python3 scripts/schema-artifacts.py bundle

# BASE=<git ref>: also check that the versions published there are unchanged.
check-schema-artifacts:
	python3 scripts/schema-artifacts.py check $(if $(BASE),--base $(BASE))

gen-claim-examples:
	python3 scripts/claim-examples.py generate

check-claim-examples:
	python3 scripts/claim-examples.py check

clean-rdf:
	scripts/clean-rdf.sh

update-graph:
	scripts/update-graph.sh

all: gen-taxonomy lint gen-doc gen-rdf check-claim-examples check-schema-artifacts update-graph
