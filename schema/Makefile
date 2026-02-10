gen-taxonomy:
	python3 scripts/populateSemanticEnums.py

lint:
	linkml-lint --validate src/ -a

gen-doc:
	gen-doc src/schema.yaml --directory generated --diagram-type mermaid_class_diagram -v

gen-rdf:
	scripts/gen-rdf.sh

clean-rdf:
	scripts/clean-rdf.sh

update-graph:
	scripts/update-graph.sh

all: gen-taxonomy lint gen-doc gen-rdf update-graph
