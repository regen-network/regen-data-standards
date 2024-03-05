# Regen Data Standards

This repository contains data standards for Regen Network.

## Taxonomies

Currently, there are two example taxonomies that can be managed in the following directories:
* Impacts: [/src/content/impact](./src/content/impact)
* Activities: [/src/content/activity](./src/content/activity)
* Ecosystems: [/src/content/ecosystem](./src/content/ecosystem)

To add new elements to the taxonomy please follow the example files in the respective directories
making sure that each element has a `title` and `image` and some descriptive text written in [Markdown](https://www.markdownguide.org).
For example for a new impact called "My Impact", you would create a file called `MyImpact.md` in the `/src/content/impact` directory with the following content:

```markdown
---
title: My Impact
image: ./myimpact.svg
---

Write the description of the element here. You can use Markdown formatting if you like
```

Make sure the image file `myimpact.svg` is in the same directory as the `MyImpact.md` file.

### Taxonomy Home Pages

Each taxonomy has a home page which describes that taxonomy, guidelines for updating it and a list of those taxonomies. These pages are located at:
* Impacts: [/src/pages/impact/index.mdx](./src/pages/impact/index.mdx)
* Activities: [/src/pages/activity/index.mdx](./src/pages/activity/index.mdx)
* Ecosystems: [/src/pages/ecosystem/index.mdx](./src/pages/ecosystem/index.mdx)
