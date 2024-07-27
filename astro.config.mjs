import {defineConfig} from 'astro/config';
import tailwind from '@astrojs/tailwind';
import pagefind from "astro-pagefind";
import mdx from '@astrojs/mdx';
import rehypeMermaid from "rehype-mermaid";
import {rehypeShiki} from "@astrojs/markdown-remark";

// https://astro.build/config
export default defineConfig({
    prefetch: true,
    integrations: [
        tailwind({}),
        pagefind(),
        mdx(),
    ],
    markdown: {
        rehypePlugins: [
            rehypeMermaid,
            rehypeShiki,
        ],
        syntaxHighlight: false,
    },
});
