import {defineConfig} from 'astro/config';
import tailwind from '@astrojs/tailwind';
import pagefind from "astro-pagefind";
import mdx from '@astrojs/mdx';
import rehypeMermaid from "rehype-mermaid";
import {rehypeShiki} from "@astrojs/markdown-remark";

// https://astro.build/config
export default defineConfig({
    build: {
        format: 'file',
    },
    prefetch: true,
    integrations: [
        tailwind({}),
        pagefind(),
        mdx(),
    ],
    redirects: {
        '/schema/[...slug].md': '/schema/[...slug]',
    },
    markdown: {
        rehypePlugins: [
            rehypeMermaid,
            rehypeShiki,
        ],
        syntaxHighlight: false,
    },
});
