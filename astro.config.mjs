import {defineConfig} from 'astro/config';
import tailwind from '@astrojs/tailwind';
import pagefind from "astro-pagefind";
import mdx from '@astrojs/mdx';

// https://astro.build/config
export default defineConfig({
    prefetch: true,
    integrations: [
        tailwind({}),
        pagefind(),
        mdx(),
    ],
});
