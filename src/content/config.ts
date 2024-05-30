import {z, defineCollection} from 'astro:content';

const commonConfig = defineCollection({
    type: 'content',
    schema: ({image}) => z.object({
        title: z.string(),
        image: image(),
    })
});

export const collections = {
    impact: commonConfig,
    activity: commonConfig,
    'environment-type': commonConfig,
}