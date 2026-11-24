# Changelog

## [1.0.0](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/compare/v0.2.0...v1.0.0) (2026-11-24)


### Features

* Add Hatch-based test matrix and coverage scripts ([1134989](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/1134989958f9b9d98037d9b54556ddc195427bbc))


### Bug Fixes

* Add REQUIRED fields to openid_configuration response ([cc6e863](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/cc6e8637d4122469509795b193f42248c84504f0))
* Align Sonar Python and coverage report path settings ([d3e6bc3](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/d3e6bc33e838d0fac41f34aa9ba5aa01ab4e4722))
* Extract per-error validator to reduce cognitive complexity ([57bebf5](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/57bebf5c2aa89d3de499038feae7d74ab9a81651))
* Extract repeated failure prefix into a constant ([f8b1bae](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/f8b1bae4a458aba5d6ad580c69c20234d163411f))
* Harden config loading and add coverage-focused tests ([8c52cfe](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/8c52cfe4cd09487c94783ca8abbf399114c8f527))
* Harden error payload validation and add helper behavior tests ([1f22330](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/1f223302f8a0817210392cdd8837558c1e2419da))
* Ignore local editor and agent metadata directories ([998b6dd](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/998b6dd32a8f29d4b0684c1d1fa2a3eb156286be))
* Modernize project license metadata for setuptools compatibility ([ceff58f](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/ceff58fb8cd073100d11c0c37028ec0d13f38afc))
* Prevent command reader task from premature collection ([c11e144](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/c11e14416200fa664497c073e008c3dd81308220))
* Remove redundant list from keycloak scopes ([dfb4982](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/dfb4982f25f39b8bd7de5203a2d78daf0767cc73))
* Run Docker container as non-root user ([cb2cf52](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/cb2cf5280a79ebd40313efb041e1cda80db70277))
* Split read_command into focused command handler functions ([cf025a3](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/cf025a388288a0e6c82af7ad1fe927bb6a2fb8eb))
* Use exec-form startup script for container command ([d1c879a](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/d1c879aedd9316bbb2f737a07a46d88b6c1ffcd5))


### Dependencies

* Add pinned test requirements file ([1d27fb0](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/1d27fb083f1737b0aefa181d26b1ee833f05e11f))
* Add pre-commit hooks for local quality checks ([6f674cd](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/6f674cd5d2b3ba748a559bb9ce076eb88b5887db))
* Add ruff configuration ([83898ec](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/83898ec7723a1c8a983aefcd9aceb0b2fab06bec))
* Migrate project dependency management to uv ([e1669f5](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/e1669f5fc1d0e153304a37e208b3d01ab43c011a))
* Update packages and simplify requirements-build setup ([a109954](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/a109954f800f6144bcfdee566f9928155685491d))


### Documentation

* Streamline PyPI publishing instructions ([da0c091](https://github.com/City-of-Helsinki/profile-gdpr-api-tester/commit/da0c091c4ce55140dcf290c8cf1226e4951efcd8))

## 0.1.0 - 2023-12-22

### Added

- Access tokens in Keycloak style, in addition to the previous Tunnistamo style. A new setting, `ISSUER_TYPE`, can be used to change the contents of access tokens.

### Fixed

- Interpret GDPR API responses according to current specification.
- OpenID configuration (`.well-known/openid-configuration`) includes all data required by the specification. (#5)
