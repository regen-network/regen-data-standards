import {defineConfig} from 'astro/config';
import tailwind from '@astrojs/tailwind';
import pagefind from "astro-pagefind";

// https://astro.build/config
export default defineConfig({
    integrations: [
        tailwind({}),
        pagefind()
    ],
});
