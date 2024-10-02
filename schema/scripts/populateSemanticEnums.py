import glob

from linkml_runtime.linkml_model import PermissibleValue
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.dumpers import yaml_dumper

# Load the taxonomy schema into a SchemaView.
taxonomy_schema_path = "../src/taxonomy.yaml"
view = SchemaView(taxonomy_schema_path)

# Map each taxonomy to the linkml enum.
taxonomies = {
    "activity": "ActivityTypes",
    "environment-type": "EnvironmentTypeTypes",
    "impact": "ImpactTypes",
}

# Load all taxonomy terms and add to the enums.
for taxonomy, enum_name in taxonomies.items():
    enum = view.get_enum(enum_name)
    md_files = glob.glob("**/*.md", root_dir=f"../../src/content/{taxonomy}", recursive=True)
    for file in md_files:
        enum_text = file.split("/").pop().replace(".md", "").replace(" ", "")
        enum_value = PermissibleValue(
            title=enum_text,
            text=enum_text,
            meaning=f"rft:{enum_text}"
        )
        enum.permissible_values.update({enum_text: enum_value})

# Write back changes to the taxonomy schema file.
with open(taxonomy_schema_path, "w") as f:
    f.write(yaml_dumper.dumps(view.schema))
