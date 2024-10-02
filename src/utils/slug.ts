export function formatSlug(slug: string): string {
    return slug.split('/').pop() ?? slug;
}