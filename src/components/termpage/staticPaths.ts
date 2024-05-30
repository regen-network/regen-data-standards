import {getCollection} from 'astro:content';
import {titleToSlug} from "../../lib/slug";

export async function getTermStaticPaths(collection: string, paramName: string) {
    const entries = await getCollection('activity');
    return entries.map(entry => {
        let res: any =  {
            params: {}, props: {entry},
        }
        const slug = titleToSlug(entry.data.title);
        console.log('slug', slug)
        res.params[paramName] = slug;
        return res;
    });
}
