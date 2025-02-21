gen-taxonomy:
	python3 scripts/populateSemanticEnums.py

lint:
	linkml-lint --validate src/ -a

gen-doc:
	gen-doc src/schemas.yaml --directory generated --diagram-type mermaid_class_diagram -v

gen-jsonld:
	linkml-convert --input-format yaml --output-format json-ld --schema src/TerrasosProjectInfo.yaml data/TerrasosProjectInfoData.yaml	--output data/TerrasosProjectInfoData.jsonld --target-class TerrasosProjectInfo

validate:
	linkml-validate -s src/TerrasosProjectInfo.yaml --target-class TerrasosProjectInfo data/TerrasosProjectInfoData.yaml

all: gen-taxonomy lint gen-doc gen-jsonld validate
