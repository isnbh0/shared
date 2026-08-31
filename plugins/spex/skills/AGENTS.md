# Spex skill maintenance

`write-phased` and `write-phased-gradual` are standalone sibling skills that
intentionally share most of their behavior.

When changing either skill, compare it with its sibling and keep their common
behavior aligned. Preserve differences that serve gradual planning's rolling frontier.

Keep their configuration examples aligned. Changes to `implement` should preserve
non-gradual behavior.
