# Changelog

## 0.2.0 - 2026-08-28

### Changed

- Added Release Please based release automation and aligned PyPI release tags to `gdpr-api-tester-v*`.
- Hardened release and CI workflows with safer dependency installation flags and pinned direct action references.
- Improved Docker runtime security by running the container as a non-root user.

## 0.1.0 - 2023-12-22

### Added

- Access tokens in Keycloak style, in addition to the previous Tunnistamo style. A new setting, `ISSUER_TYPE`, can be used to change the contents of access tokens.

### Fixed

- Interpret GDPR API responses according to current specification.
- OpenID configuration (`.well-known/openid-configuration`) includes all data required by the specification. (#5)
