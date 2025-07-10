gen-taxonomy:
	python3 scripts/populateSemanticEnums.py

lint:
	linkml-lint --validate src/ -a

gen-doc:
	gen-doc src/schema.yaml --directory generated --diagram-type er_diagram -v

gen-rdf:
	scripts/gen-rdf.sh

all: gen-taxonomy lint gen-doc gen-rdf
