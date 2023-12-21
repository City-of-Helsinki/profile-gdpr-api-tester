# Changelog

## 0.1.0 - 2023-12-22

### Added

- Access tokens in Keycloak style, in addition to the previous Tunnistamo style. A new setting, `ISSUER_TYPE`, can be used to change the contents of access tokens.

### Fixed

- Interpret GDPR API responses according to current specification.
- OpenID configuration (`.well-known/openid-configuration`) includes all data required by the specification. (#5)
