gen-taxonomy:
	python3 scripts/populateSemanticEnums.py

lint:
	linkml-lint --validate src/ -a

gen-doc:
	gen-doc src/schemas.yaml --directory generated --diagram-type er_diagram -v

gen-jsonld:
	linkml-convert --input-format yaml --output-format json-ld --schema src/TerrasosProjectInfo.yaml data/TerrasosProjectInfoData.yaml	--output data/TerrasosProjectInfoData.jsonld --target-class TerrasosProjectInfo

validate:
	linkml-validate -s src/schemas.yaml --target-class BT01ProjectInfo data/BT01ProjectInfoData.yaml
	linkml-validate -s src/schemas.yaml --target-class CreditClassInfo data/BT01.jsonld

all: gen-taxonomy lint gen-doc gen-jsonld validate
