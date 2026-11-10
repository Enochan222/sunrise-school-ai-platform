# Platform Release Manifest Owner Matrix — Generated from Stage Registry

A B I U service codebase and database schema changes must be isolated. Other owners' SHA/Image/Schema/Config remain pinned from prior approved Platform Release; if an API change is required, add an earlier owner-specific Release and rerun contract tests. Stage0 is Docs only, no Product Release.

| Release | Owner changed | A Vault | B Operations | I Integration | U Frontend |
|---|---|---|---|---|---|
| R01 | **A** | CHANGE | NOT DEPLOYED | NOT DEPLOYED | NOT DEPLOYED |
| R02 | **A** | CHANGE | NOT DEPLOYED | NOT DEPLOYED | NOT DEPLOYED |
| R03 | **B** | FROZEN | CHANGE | NOT DEPLOYED | NOT DEPLOYED |
| R04 | **I** | FROZEN | FROZEN | CHANGE | NOT DEPLOYED |
| R05 | **U** | FROZEN | FROZEN | FROZEN | CHANGE |
| R06 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R07 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R08 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R09 | **I** | FROZEN | FROZEN | CHANGE | FROZEN |
| R10 | **U** | FROZEN | FROZEN | FROZEN | CHANGE |
| R11 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R12 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R13 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R14 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R15 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R16 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R17 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R18 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R19 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R20 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R21 | **U** | FROZEN | FROZEN | FROZEN | CHANGE |
| R22 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R23 | **I** | FROZEN | FROZEN | CHANGE | FROZEN |
| R24 | **U** | FROZEN | FROZEN | FROZEN | CHANGE |
| R25 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R26 | **A** | CHANGE | FROZEN | FROZEN | FROZEN |
| R27 | **B** | FROZEN | CHANGE | FROZEN | FROZEN |
| R28 | **I** | FROZEN | FROZEN | CHANGE | FROZEN |


**One Owner changed** is a runtime deployment property, not an assertion that only one service executed API calls. B and A can be exercised in an I E2E test without modifying their code/DDL. Source/Schema migrations after a release require compatibility checks and explicit rollback/forward-fix evidence.
