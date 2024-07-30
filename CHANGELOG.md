# Changelog

## v0.4.3 (July 2024

This release simply re-enables Firefox testing in the CI, and reorganises the associated cloud runs.

## What's Changed
* Re-enable Firefox e2e tests by @ml-evs in https://github.com/datalab-org/datalab/pull/711

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.4.2...v0.4.3


## v0.4.2 (July 2024)

This release adds an update to the batch item creation UI to include other item types, and includes a new preview of the tabular UI which can be accessed at the path `/next`, as well as several UI tweaks and fixes.

## What's Changed

* Rebrand repo to the group-agnostic gh organisation by @ml-evs in https://github.com/datalab-org/datalab/pull/809
* Change docker compose restart policy to "unless-stopped" by @ml-evs in https://github.com/datalab-org/datalab/pull/810
* Update INSTALL.md by @jdbocarsly in https://github.com/datalab-org/datalab/pull/816
* Fix logo link taking full screen width by @ml-evs in https://github.com/datalab-org/datalab/pull/821
* Improve sample table component by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/784
* Add simple component test for `ChemFormInput` by @ml-evs in https://github.com/datalab-org/datalab/pull/743
* Add ability to add batch of cells by @jdbocarsly in https://github.com/datalab-org/datalab/pull/797
* Add config options to automatically activate accounts from GitHub, email or any auth source by @ml-evs in https://github.com/datalab-org/datalab/pull/822
* Bump version number to 0.4.2 by @ml-evs in https://github.com/datalab-org/datalab/pull/824

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.4.1...v0.4.2

## v0.4.1 (July 2024)

This minor release adds some quality-of-life fixes to the UI, a new cell format type "in situ (optical)" and tweaks to our development workflow.

## What's Changed

* Run vue3-recommended linting by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/756
* Corrected blockInfo computed property value by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/775
* Changes to pre-commit  by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/785
* Add 'optical' cellFormat by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/788
* Remove cheminventory import task (which is now in `datalab-api`) by @ml-evs in https://github.com/the-grey-group/datalab/pull/793
* Add gpt4o and other updated models by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/736
* Report runtime server config at `/info` and use this in UI by @ml-evs in https://github.com/the-grey-group/datalab/pull/801
* Development docker, pre-commit and eslint updates & refactoring by @ml-evs in https://github.com/the-grey-group/datalab/pull/805
* Disable `ChemicalFormula` component by @ml-evs in https://github.com/the-grey-group/datalab/pull/806

**Full Changelog**: https://github.com/the-grey-group/datalab/compare/v0.4.0...v0.4.1

## v0.4.0 (June 2024)

This release of *datalab* contains significant new functionality whilst broadly maintaining compatibility with the 0.3.x series.

It is also accompanied by the first release of the *datalab* Python API package (https://github.com/datalab-org/datalab-api), as well as the first release of the Ansible playbooks and Terraform rules (Azure only, for now) to automated *datalab* deployments (https://github.com/datalab-org/datalab-ansible-terraform).

Special thanks go to @vrajpatel9988 and especially @BenjaminCharmes who both made their first contributions to *datalab* in this release!

### Highlights

- User accounts: users can now update their name and contact info, as well as connect external accounts and regenerate API keys directly from the web UI. The ability to login via ORCID is now enabled by default (but must be configured at the instance level).
- Admin dashboard: adds the ability for admins to do user management from the UI directly.
- Electrochemistry block: support for Neware file formats, MPR files written by ECLab > 11.50 and cyclic voltammetry data.
- Equipment: A new entry type has been added to record the equipment in the lab used for certain operations
- Better default permissions on inventories: users can now create and edit inventory entries without requiring an admin.
- Automatic random IDs: The ability to generate random IDs for new samples was added, allowing *datalab* to be used as the source of IDs.
- Enhanced block-level documentation in the UI, and dynamic syncing of block-type metadata for improved extensibility.
- Added the admin ability to verify all user accounts before they can use *datalab*.
- General improvements to block error reporting and reactivity, as well as several bug fixes.


### Notes for upgrading to v0.4.0

- Users now have an `"unverified"` status by default. For some deployments, this may require an admin to first self-verify their account directly with a database update (`"account_status" -> "active"`), after which they can verify all other users in the UI.
- The data mount point of the `database` container in the default `./docker-compose.yml` has changed to use `/data/db` on the host system. Deployments using this configuration should be careful to backup and restore from their existing database, or continue to use the `docker volume` approach (feel free to raise an issue with any questions).
- Similarly, the development set up has changed slightly and may need to be remade after upgrading.

### What's Changed
* Dynamically set production app container config in entrypoint by @ml-evs in https://github.com/the-grey-group/datalab/pull/605
* Visual style improvements, test updates and improved block UI by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/608
* Refactor mail config settings by @ml-evs in https://github.com/the-grey-group/datalab/pull/614
* Add Neware support and fix MPR issue by @ml-evs in https://github.com/the-grey-group/datalab/pull/617
* Hotfix for block errors and warnings UI that arise over multiple renderings by @ml-evs in https://github.com/the-grey-group/datalab/pull/615
* Use newly released galvani and NewareNDA packages by @ml-evs in https://github.com/the-grey-group/datalab/pull/625
* Update xrdml parser so it works with v2.0 by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/631
* Restrict relationship types in UI synthesis and constituents tables by @ml-evs in https://github.com/the-grey-group/datalab/pull/630
* Update copyright year in LICENSE by @ml-evs in https://github.com/the-grey-group/datalab/pull/622
* Allow browser context menu in tinymce fields by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/635
* Allow any authenticated user to generate an API key by @ml-evs in https://github.com/the-grey-group/datalab/pull/641
* Serve the identifier prefix in the `/info` response by @ml-evs in https://github.com/the-grey-group/datalab/pull/638
* Return user role from `/get-current-user` endpoint by @ml-evs in https://github.com/the-grey-group/datalab/pull/644
* Created component for editing account settings by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/627
* User registration: default display name to GitHub username when no profile name is set by @ml-evs in https://github.com/the-grey-group/datalab/pull/655
* Fix typo where CI tests were never run in chrome by @ml-evs in https://github.com/the-grey-group/datalab/pull/656
* Temporarily disable Firefox tests by @ml-evs in https://github.com/the-grey-group/datalab/pull/659
* Bump webpack-dev-middleware from 5.3.3 to 5.3.4 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/660
* Bump follow-redirects from 1.15.4 to 1.15.6 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/647
* Allow echem block to plot non-cyclic data by @ml-evs in https://github.com/the-grey-group/datalab/pull/665
* Add optional functionality to add starting materials from within the webapp by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/642
* Added validation for the user update route/UI by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/646
* Improve block warning/error reactivity in the UI by @ml-evs in https://github.com/the-grey-group/datalab/pull/666
* Add ability to generate .csv files within block callbacks by @ml-evs in https://github.com/the-grey-group/datalab/pull/621
* Debug flaky e2e tests by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/670
* Add option to generate ID automatically when creating items  by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/668
* Add default config for `VUE_APP_EDITABLE_INVENTORY` by @ml-evs in https://github.com/the-grey-group/datalab/pull/673
* Add codecov upload to CI by @ml-evs in https://github.com/the-grey-group/datalab/pull/677
* Disable codecov PR annotations by @ml-evs in https://github.com/the-grey-group/datalab/pull/681
* Add "equipment" item type by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/531
* Convert Whinchat to use langchain  by @vrajpatel9988 in https://github.com/the-grey-group/datalab/pull/661
* Bump langchain-core from 0.1.33 to 0.1.35 in /pydatalab by @dependabot in https://github.com/the-grey-group/datalab/pull/686
* Bump prettier, pre-commit hooks and some other deps by @ml-evs in https://github.com/the-grey-group/datalab/pull/685
* Allow starting materials and equipment to be edited by normal users by @ml-evs in https://github.com/the-grey-group/datalab/pull/672
* Bump pymongo from 4.6.2 to 4.6.3 in /pydatalab by @dependabot in https://github.com/the-grey-group/datalab/pull/689
* Use mocked API keys in API tests to fake different authentication scenarios  by @ml-evs in https://github.com/the-grey-group/datalab/pull/676
* Significant refactor of deployment docs  by @ml-evs in https://github.com/the-grey-group/datalab/pull/690
* Enable ORCID connection by default by @ml-evs in https://github.com/the-grey-group/datalab/pull/693
* Only fix PRs with pre-commit CI when asked by @ml-evs in https://github.com/the-grey-group/datalab/pull/697
* Upgrade cypress and other testing deps to allow Firefox testing by @ml-evs in https://github.com/the-grey-group/datalab/pull/699
* Update README with links to Python API by @ml-evs in https://github.com/the-grey-group/datalab/pull/701
* Add public deployment badge in README by @ml-evs in https://github.com/the-grey-group/datalab/pull/702
* Separate each browser test into separate run and temporarily disable Firefox by @ml-evs in https://github.com/the-grey-group/datalab/pull/703
* Add admin dashboard with user management controls by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/674
* Added a way to refresh API Key from Account Settings UI by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/700
* Recreate user index with new settings if already existing by @ml-evs in https://github.com/the-grey-group/datalab/pull/707
* Fix for saving collection blocks and error handling for excessively large blocks by @ml-evs in https://github.com/the-grey-group/datalab/pull/709
* Add `account_status` field (active, unverified or deactivated) to People model by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/687
* Update deployment instructions wrt. new datalab-ansible-terraform repo by @ml-evs in https://github.com/the-grey-group/datalab/pull/712
* Add UI for email registration/login by @ml-evs in https://github.com/the-grey-group/datalab/pull/528
* Serve data about available block types in API by @ml-evs in https://github.com/the-grey-group/datalab/pull/667
* Add upper pin to rosettasciio by @ml-evs in https://github.com/the-grey-group/datalab/pull/720
* Update tests for current user by @ml-evs in https://github.com/the-grey-group/datalab/pull/723
* Add ability to select between different chat models in the whinchat by @vrajpatel9988 in https://github.com/the-grey-group/datalab/pull/680
* Bump Flask and Werkzeug to the latest releases on the v3 series by @ml-evs in https://github.com/the-grey-group/datalab/pull/722
* Added `HelpBubble` component to display inline documentation in the UI by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/706
* Fix API key help message by @ml-evs in https://github.com/the-grey-group/datalab/pull/725
* Fix README badges by @ml-evs in https://github.com/the-grey-group/datalab/pull/730
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/the-grey-group/datalab/pull/728
* Revert pre-commit autoupdate for prettier by @ml-evs in https://github.com/the-grey-group/datalab/pull/734
* Populating dynamic block-level documentation as UI tooltips by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/719
* Make account status on registration be configurable by provider by @ml-evs in https://github.com/the-grey-group/datalab/pull/733
* Add notification-dot for user with unverified account_status by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/724
* Consider account status during auth and refactor API around blueprints by @ml-evs in https://github.com/the-grey-group/datalab/pull/727
* Add gravatar instructions and tweak account settings modal by @ml-evs in https://github.com/the-grey-group/datalab/pull/744
* Add block help to block title by @ml-evs in https://github.com/the-grey-group/datalab/pull/737
* Fix NMR block layout issue by @ml-evs in https://github.com/the-grey-group/datalab/pull/745
* Fix issue with landing page and tweak default docker-compose deployment by @ml-evs in https://github.com/the-grey-group/datalab/pull/746
* Improve admin dashboard styling and functionality by @BenjaminCharmes in https://github.com/the-grey-group/datalab/pull/748
* Add `API_URL` as a `meta` tag in HTML header of all UI responses by @ml-evs in https://github.com/the-grey-group/datalab/pull/750
* Add `CONFIG.APP_URL` to allow for customisable redirects on login/registration by @ml-evs in https://github.com/the-grey-group/datalab/pull/749
* Fix StyledInput component (v2) by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/751
* Bump version numbers by @ml-evs in https://github.com/the-grey-group/datalab/pull/753
* Add a Tabular data block that can handle simple CSVs and text files by @ml-evs in https://github.com/the-grey-group/datalab/pull/592
* Remove GET-out of route permissions by @ml-evs in https://github.com/the-grey-group/datalab/pull/754
* Tweak mount points, production Docker entrypoint and development environment by @ml-evs in https://github.com/the-grey-group/datalab/pull/763
* Default to ORCID ID as display name when ORCID user's name is private by @ml-evs in https://github.com/the-grey-group/datalab/pull/769
* Add process lock for remote filesystem scraper by @ml-evs in https://github.com/the-grey-group/datalab/pull/562
* Bump version number to v0.4.0 by @ml-evs in https://github.com/the-grey-group/datalab/pull/770

### New Contributors
* @BenjaminCharmes made their first contribution in https://github.com/the-grey-group/datalab/pull/627
* @vrajpatel9988 made their first contribution in https://github.com/the-grey-group/datalab/pull/661

**Full Changelog**: https://github.com/the-grey-group/datalab/compare/v0.3.2...v0.4.0

## v0.3.2 (February 2024)

This is a build hotfix for 0.3.x, where the incorrect versions of `navani` and `galvani` were being installed in docker builds (leading to missing support for ECLab >= 11.50).

### What's Changed

* Force galvani and navani update in lockfile by @ml-evs in https://github.com/the-grey-group/datalab/pull/602


**Full Changelog**: https://github.com/the-grey-group/datalab/compare/v0.3.1...v0.3.2

## v0.3.1 (February 2024)

This release makes a few fixes relative to 0.3.0, primarily around file uploads and internal database storage.

It also adds the ability for data blocks to pass errors and warnings to the front-end, which can be useful for helping describe incompatibilities in data, analysis or plotting dynamically.

### What's Changed

* Pin prettier version in Webapp to same version that is specified in pre-commit by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/589
* Downgrade pre-commit prettier by @ml-evs in https://github.com/the-grey-group/datalab/pull/593
* CSS cleanup by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/588
* Fix issue where plot data was always stored in db by @ml-evs in https://github.com/the-grey-group/datalab/pull/599
* Add ability for block errors and warnings to be passed through API to UI by @ml-evs in https://github.com/the-grey-group/datalab/pull/590
* Fix issue where previously uploaded file cannot be replaced by @ml-evs in https://github.com/the-grey-group/datalab/pull/594

**Full Changelog**: https://github.com/the-grey-group/datalab/compare/v0.3.0...v0.3.1

## v0.3.0 (Feburary 2024)

This is the long overdue v0.3.0 release of datalab, which coincides with many new deployments popping up. It is strongly recommended to upgrade and continue to keep up-to-date with releases as they come out. There are no intentional breaking changes between this release and the previous release candidates, so please report any issues you come across on the [GitHub issue tracker](https://github.com/the-grey-group/datalab/issues).

Thanks to new contributor @elbee99 who has added support for Raman spectroscopy, plus new contributors with as-of-yet unreleased changes!

### Highlights

- Support for Biologic data files created with the most recent versions of ECLab 11.50+, plus enhanced support for Arbin data files
- A new 1D Raman block that can parse both Renishaw WDF and Oxford Instrument's spectra
- Ability to group samples and other entries into collections
- Support for new authentication methods, such as magic links via email
- Significant refactoring and modularization to ease the process of new contributions
- Simplified deployment procedure via Docker
- Automated snapshot backups


### What's changed?

* Add concept of user manager permissions by @ml-evs in https://github.com/the-grey-group/datalab/pull/417
* Add UI for collections, fix local graphs and improve tables by @ml-evs in https://github.com/the-grey-group/datalab/pull/404
* Adjust default echem subsampling by @ml-evs in https://github.com/the-grey-group/datalab/pull/426
* Version bumps and linting tweaks by @ml-evs in https://github.com/the-grey-group/datalab/pull/429
* Remote filesystem scanning improvements by @ml-evs in https://github.com/the-grey-group/datalab/pull/430
* Implemented Raman block by @elbee99 in https://github.com/the-grey-group/datalab/pull/422
* Move echem block to its own app submodule by @ml-evs in https://github.com/the-grey-group/datalab/pull/433
* Switch from flake8+isort to ruff by @ml-evs in https://github.com/the-grey-group/datalab/pull/434
* Update vue/cli to v5 by @ml-evs in https://github.com/the-grey-group/datalab/pull/432
* Tweak to remote file system caching for improved page loads by @ml-evs in https://github.com/the-grey-group/datalab/pull/435
* Enable Arbin res file parsing by adding mdbtools/0.7.1 build to server Dockerfile  by @ml-evs in https://github.com/the-grey-group/datalab/pull/436
* Better sanitize inputs for plot cycle selector by @ml-evs in https://github.com/the-grey-group/datalab/pull/438
* Add sample/user/cell counters to deployment about page by @ml-evs in https://github.com/the-grey-group/datalab/pull/383
* Fix last modified timezone and make value dynamic by @ml-evs in https://github.com/the-grey-group/datalab/pull/439
* Restructure NMR block module and add tests by @ml-evs in https://github.com/the-grey-group/datalab/pull/441
* Add basic permissions to files  by @ml-evs in https://github.com/the-grey-group/datalab/pull/445
* Fix broken README link and update affiliations by @ml-evs in https://github.com/the-grey-group/datalab/pull/448
* Manual overhaul of API docs by @ml-evs in https://github.com/the-grey-group/datalab/pull/451
* Fix bug where user cannot be created with blank display name by @ml-evs in https://github.com/the-grey-group/datalab/pull/456
* Bump navani and try to accomodate other deps by @ml-evs in https://github.com/the-grey-group/datalab/pull/457
* Update INSTALL.md by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/458
* Add subtitled intro video to README by @ml-evs in https://github.com/the-grey-group/datalab/pull/459
* Bump @babel/traverse from 7.22.10 to 7.23.2 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/463
* Bump apollo-server-core from 3.12.0 to 3.12.1 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/446
* Bump tinymce from 5.10.7 to 5.10.8 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/465
* Support .wdf files for 1D Raman by @elbee99 in https://github.com/the-grey-group/datalab/pull/466
* Add more details to README by @ml-evs in https://github.com/the-grey-group/datalab/pull/479
* Adding limits on file uploads by @ml-evs in https://github.com/the-grey-group/datalab/pull/475
* Improve login/logout UI to support multiple authentication mechanisms by @ml-evs in https://github.com/the-grey-group/datalab/pull/384
* Remove unecessary scope for GitHub OAuth by @ml-evs in https://github.com/the-grey-group/datalab/pull/483
* Tweak to deployed documentation by @ml-evs in https://github.com/the-grey-group/datalab/pull/485
* Revamp installation docs with additional configuration/administration/deployment info by @ml-evs in https://github.com/the-grey-group/datalab/pull/490
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/the-grey-group/datalab/pull/493
* Bump browserify-sign from 4.2.1 to 4.2.2 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/480
* Rework e2e tests by @ml-evs in https://github.com/the-grey-group/datalab/pull/504
* CI build optimisations by @ml-evs in https://github.com/the-grey-group/datalab/pull/497
* Fix file permissions issues by @ml-evs in https://github.com/the-grey-group/datalab/pull/511
* Labspec 1D Raman compatibility by @elbee99 in https://github.com/the-grey-group/datalab/pull/477
* Make sure cypress cloud runs are recorded by @ml-evs in https://github.com/the-grey-group/datalab/pull/515
* Clarify refcode prefix docs and config by @ml-evs in https://github.com/the-grey-group/datalab/pull/516
* Add note about GitHub callback URL in docs by @ml-evs in https://github.com/the-grey-group/datalab/pull/517
* Bump to cypress 13 and remove flaky tests in CI by @ml-evs in https://github.com/the-grey-group/datalab/pull/519
* Additionally e2e test Firefox & Chrome by default by @ml-evs in https://github.com/the-grey-group/datalab/pull/521
* Improve GitHub OAuth connection by @ml-evs in https://github.com/the-grey-group/datalab/pull/523
* Fix scope order for GitHub OAuth app by @ml-evs in https://github.com/the-grey-group/datalab/pull/525
* Generate default `SECRET_KEY` from platform-specific info by @ml-evs in https://github.com/the-grey-group/datalab/pull/527
* Make Flask session lifetime configurable by @ml-evs in https://github.com/the-grey-group/datalab/pull/526
* Add ability to register and sign-in via email magic links by @ml-evs in https://github.com/the-grey-group/datalab/pull/484
* Check and warn for missing secrets in server startup logs by @ml-evs in https://github.com/the-grey-group/datalab/pull/529
* Miscellaneous tidying by @ml-evs in https://github.com/the-grey-group/datalab/pull/532
* remove option to add a "Test Block" on the edit page by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/535
* Promote `invoke` to a real dependency rather than dev dependency by @ml-evs in https://github.com/the-grey-group/datalab/pull/541
* Fix `y_options` bug when plotting 1D Raman by @ml-evs in https://github.com/the-grey-group/datalab/pull/542
* Native support for automatic backups by @ml-evs in https://github.com/the-grey-group/datalab/pull/467
* Add rotating file log handler and simplify streamed log messages by @ml-evs in https://github.com/the-grey-group/datalab/pull/545
* Update backup docs by @ml-evs in https://github.com/the-grey-group/datalab/pull/544
* Bump follow-redirects from 1.15.2 to 1.15.4 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/533
* Bump tinymce from 5.10.8 to 5.10.9 in /webapp by @dependabot in https://github.com/the-grey-group/datalab/pull/508
* Update galvani to 0.3.0 by @ml-evs in https://github.com/the-grey-group/datalab/pull/551
* Pin `openai` to 0.28 until we can migrate by @ml-evs in https://github.com/the-grey-group/datalab/pull/555
* Bump aiohttp from 3.9.1 to 3.9.2 in /pydatalab by @dependabot in https://github.com/the-grey-group/datalab/pull/559
* Add UI for adding an existing item to an existing collection by @ml-evs in https://github.com/the-grey-group/datalab/pull/553
* Bump navani to support ECLab >= 11.50 by @ml-evs in https://github.com/the-grey-group/datalab/pull/563
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/the-grey-group/datalab/pull/564
* Add spacing above logo by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/575
* Tweaks and bugfixes for collection assignment UI, badge styles and navbar by @jdbocarsly in https://github.com/the-grey-group/datalab/pull/566
* Add drop shadow to badge hover  by @ml-evs in https://github.com/the-grey-group/datalab/pull/579
* Upgrade mdbtools per new galvani version by @ml-evs in https://github.com/the-grey-group/datalab/pull/581
* Disable ORCID sign-in UI for now by @ml-evs in https://github.com/the-grey-group/datalab/pull/580
* Prepare 0.3.0 release by @ml-evs in https://github.com/the-grey-group/datalab/pull/583

### New Contributors
* @elbee99 made their first contribution in https://github.com/the-grey-group/datalab/pull/422
* @pre-commit-ci made their first contribution in https://github.com/the-grey-group/datalab/pull/493

**Full Changelog**: https://github.com/the-grey-group/datalab/compare/v0.2.5...v0.3.0
