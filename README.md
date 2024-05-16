# Regen Data Standards

This repository contains data standards for Regen Network.

## Taxonomies

Taxonomy cards are intended to provide a high-level sense of a project’s activities, environment, and impact. The labels and associated definitions and icons convey a general idea rather than provide an analytical understanding. For more details about a project’s activities, environment, and impact, it will be necessary to read the relevant project documentation.

Taxonomies can be managed in the following directories dedicated to the three taxonomy card types:
* Impacts: [/src/content/impact](./src/content/impact)
* Activities: [/src/content/activity](./src/content/activity)
* Environment Type: [/src/content/environment-type](./src/content/environment-type)

Each taxonomy card type can have hierarchical relationships, which will be useful when selecting, searching, and grouping terms on the web page. Below is an example. For example, if the top level of the hierarchy is “Marine,” and sub-categories under that are "Coastal", "Coral Reef", and "Deep Water". The terms for each of those levels needs a definition.

In the above example, the Marine.md file would go into the “environment-type” directory (/src/content/environment-type/Marine.md) and the CoralReef.md file would go in the “Marine” directory (/src/content/environment-type/Marine/CoralReef.md)

To add new elements to the taxonomy please follow the example files in the respective directories
making sure that each element has a `title` and icon `image` and some descriptive text written in [Markdown](https://www.markdownguide.org).
For example for a new impact called "My Impact", you would create a file called `MyImpact.md` in the `/src/content/impact` directory with the following content:

```markdown
---
title: My Impact
image: ./myimpact.svg
---

Write the description of the element here. You can use Markdown formatting if you like
```

Make sure the icon image file `myimpact.svg` is in the same directory as the `MyImpact.md` file.

### Taxonomy Home Pages

Each taxonomy has a home page which describes that taxonomy, guidelines for updating it and a list of those taxonomies. These pages are located at:
* Impacts: [/src/pages/impact/index.mdx](./src/pages/impact/index.mdx)
* Activities: [/src/pages/activity/index.mdx](./src/pages/activity/index.mdx)
* Environment Type: [/src/pages/environment-type/index.mdx](./src/pages/environment-type/index.mdx)
