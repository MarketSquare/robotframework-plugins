## REMOVED Requirements

### Requirement: The rf-agentskills bundle keeps existing installs whole

**Reason**: Few users adopted the bundle. It doubled every skill change with a generated copy under `bundles/`, needed its own release, and had to grow with every new plugin. The project is still being set up, so the bundle is removed without a deprecation period.

**Migration**: Install `rf-core` and the technology plugins you need (`rf-web`, `rf-api`, `rf-mobile`, `rf-desktop`) from the `robotframework-plugins` marketplace, or run `robotframework-plugins install`. Skills carry their plugin's prefix (`rf-web:rf-browser` instead of `rf-agentskills:rf-browser`), so update project instructions that name a prefixed skill. Claude Code uninstalls `rf-agentskills` on its next marketplace update, because the marketplace no longer lists it.
