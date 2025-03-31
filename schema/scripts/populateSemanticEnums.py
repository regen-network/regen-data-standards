import glob
import re

from linkml_runtime.linkml_model import PermissibleValue
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.dumpers import yaml_dumper

# Load the taxonomy schema into a SchemaView.
taxonomy_schema_path = "src/taxonomy.yaml"
view = SchemaView(taxonomy_schema_path)

# Map each taxonomy to the linkml enum.
taxonomies = {
    "activity": "ActivityType",
    "environment-type": "EnvironmentType",
    "impact": "ImpactType",
}

# Load all taxonomy terms and add to the enums.
for taxonomy, enum_name in taxonomies.items():
    enum = view.get_enum(enum_name)
    md_files = glob.glob("**/*.md", root_dir=f"../src/content/{taxonomy}", recursive=True)
    for file in md_files:
        enum_name = file.split("/").pop().replace(".md", "").replace(" ", "")
        enum_key = re.sub('([A-Z])', r'_\1', enum_name).lstrip("_").upper()
        enum_value = PermissibleValue(
            title=enum_name,
            text=enum_key,
            meaning=f"rft:{enum_name}"
        )
        enum.permissible_values.update({enum_key: enum_value})

# Write back changes to the taxonomy schema file.
with open(taxonomy_schema_path, "w") as f:
    f.write(yaml_dumper.dumps(view.schema))
