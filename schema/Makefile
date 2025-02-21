gen-taxonomy:
	python3 scripts/populateSemanticEnums.py

lint:
	linkml-lint --validate src/ -a

gen-doc:
	gen-doc src/schemas.yaml --directory generated --diagram-type mermaid_class_diagram -v

gen-jsonld:
	linkml-convert --input-format yaml --output-format json-ld --schema src/schema.yaml data/BT01ProjectInfoData.yaml	--output data/BT01ProjectInfoData.jsonld --target-class BT01ProjectInfo

validate:
	linkml-validate -s src/schema.yaml --target-class BT01ProjectInfo data/BT01ProjectInfoData.yaml

all: gen-taxonomy lint gen-doc gen-jsonld validate
