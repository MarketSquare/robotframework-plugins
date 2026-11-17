## ADDED Requirements

### Requirement: Keyword checks point to robotcode

The skill SHALL tell the agent, in its main text before the keyword reference and not only in its closing section, to check a PlatynUI keyword's name and arguments with `robotcode doc keyword PlatynUI.BareMetal "<Keyword>"` (and to search with `robotcode doc keywords PlatynUI.BareMetal "<text>"`), and not by parsing a libdoc file or reading library source.

#### Scenario: Lookup guidance near the keyword reference
- **WHEN** SKILL.md is read up to the start of the Core Keywords Quick Reference
- **THEN** it has already named `robotcode doc keyword PlatynUI.BareMetal` as the way to verify a keyword and its arguments
