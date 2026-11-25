// Page-side value types, free of DOM and Vite types so Node-side tests can import them.
export type DocId = string & { readonly __brand: "DocId" };
export type Rev = string & { readonly __brand: "Rev" };
export type Doc = { id: DocId; name: string; path: string };
export type Disk = { rev: Rev; text: string } | { rev: null };
