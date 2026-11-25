# Vendored Mermaiden

`mermaiden/` and `mermaiden-toolkit/` are the packed contents of those two packages from the
Mermaiden repository. Neither is published to npm, so `package.json` depends on them by `file:`
path. Mermaid itself still comes from npm, as the peer dependency the vendored packages declare.

`SOURCE` records the commit the copies came from. Both packages are MIT, and each keeps its own
`LICENSE`.

## Refresh

    MERMAIDEN_DIR=~/local/src/mermaiden vendor/update.sh

The script builds the packages in that checkout, packs them, replaces both directories, and
rewrites `SOURCE`. After it, run `pnpm install`, `pnpm check`, and `wb stop`.
