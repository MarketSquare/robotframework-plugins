## MODIFIED Requirements

### Requirement: A missing stable ref names the alternatives

`fetch()` SHALL keep `stable` as its default ref. When `stable` is not found in the repository, the `FetchError` SHALL say that `stable` is missing and name `latest` or a release tag (`v<version>`) as the refs to use instead. The installer README and the repository README SHALL say that every release moves `stable`.

#### Scenario: Default ref before the first release
- **WHEN** the repository has no `stable` ref and a tool calls `fetch()`
- **THEN** it raises `FetchError` whose message names `stable`, `latest` and a release tag

## ADDED Requirements

### Requirement: Catalogue entries keep their keys without bundles

`bundle.catalog()` and `Snapshot.catalog()` entries SHALL keep the `bundle` and `bundled` keys, with the values `false` and `[]`, so that `bundle.CATALOG_FORMAT` stays `1` and tools that read the keys keep working. The keys SHALL be dropped only together with a change of `CATALOG_FORMAT`.

#### Scenario: Keys present and constant
- **WHEN** `bundle.catalog()` is called on a release without bundles
- **THEN** every entry has `bundle` equal to `false` and `bundled` equal to `[]`, and `bundle.CATALOG_FORMAT` is `1`
