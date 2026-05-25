# Changelog

> [!NOTE]
> Release candidates are not included in this changelog; there may be more
recent changes described in the [release notes on GitHub](https://github.com/datalab-org/datalab/releases).

## v0.7.0 (May 2026)

This is a major release with significant new functionality, refined over many months and pre-releases.
This release roughly coincides with the publication of our preprint on *datalab*, available from ChemRxiv:

> Matthew L. Evans, Joshua D. Bocarsly, Benjamin Charmes, Ben E. Smith, Gian-Marco Rignanese, David Waroquiers, Clare P. Grey, **datalab: Federated data management infrastructure for materials chemistry and beyond**, ChemRxiv (2026). DOI: [10.26434/chemrxiv.15001945/v1](https://doi.org/10.26434/chemrxiv.15001945/v1)

The headline changes are:

- Users can now be assigned to groups, and groups can be given read permissions over different items and collections
- [ELN file format exports](https://github.com/TheELNConsortium/TheELNFileFormat): collections, items and subgraphs of an item's relationships can now be exported in a single .eln zip file, with all attached data and metadata.
- Revision control of items: updating an item now triggers a version snapshot, which can be rolled back to at any time.
- New plugin build system for easier customisation of *datalab* instances.
- Item models:
    - Status fields for items (e.g., active, disposed, planned, ordered)
    - New substance fields and UI for recording hazards and chemical identifiers (CAS, SMILES, Inchi, InchiKey)
- Data block updates:
    - New measurement types:
        - Cyclic voltammetry,
        - XPS,
    - Support for new file formats:
        - [Battery Data Format (BDF)](https://battery-data-alliance.github.io/battery-data-format/) for time-series cycling data,
        - Bruker's .raw and .brml files for XRD,
        - Neware cycler Excel exports,
        - JEOL's NMR format,
        - BioLogic .mpr for EIS measurements,
        - .vgd files for XPS.
    - The NMR block now supports auto-phasing and processing of raw FID data.
- An experimental backend for processing block data asynchronously (see [Asynchronous Processing](blocks/index.md#asynchronous-processing-experimental)).

In addition, there are several new plugins available, many of which can be found on the GitHub [`datalab-plugins` topic](https://github.com/topics/datalab-plugin).

There is also a new tool called [`beholder`](https://github.com/datalab-industries/datalab-beholder) which can be configured to perform automated data capture, as well as several improvements to the cloud deployment rules at [datalab-ansible-terraform](https://github.com/datalab-industries/datalab-ansible-terraform).

### What's Changed

* Minor fix for email auth notifications with automatically activated accounts by @ml-evs in https://github.com/datalab-org/datalab/pull/1473
* Enable flake8-logging-rules (G) in ruff by @ml-evs in https://github.com/datalab-org/datalab/pull/1202
* Update funding info in README.md by @jdbocarsly in https://github.com/datalab-org/datalab/pull/1487
* Add error handling for file upload size limits by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1472
* Add status field for items and equipment by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/866
* Update About page with README acknowledgements by @ml-evs in https://github.com/datalab-org/datalab/pull/1490
* Remove defunct mongomock local testing config by @ml-evs in https://github.com/datalab-org/datalab/pull/1492
* Explicitly copy any private plugins into API docker build by @ml-evs in https://github.com/datalab-org/datalab/pull/1495
* Add button to save csv for differential echem by @ml-evs in https://github.com/datalab-org/datalab/pull/1498
* Fix NotificationDot positioning in user dropdown menu by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1484
* Fix copied items with blocks getting wrong IDs by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1475
* Add contribution graph visualization for user and community activity by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1461
* Add CRUD API for user groups by @ml-evs in https://github.com/datalab-org/datalab/pull/1493
* Add read-only group permissions model for items by @ml-evs in https://github.com/datalab-org/datalab/pull/1499
* UI for creating and adminstering user groups and item permissions by @ml-evs in https://github.com/datalab-org/datalab/pull/1500
* Fix XRD block legend display issues by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1489
* Add icon counters for blocks and files in collection items table by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1471
* Update Person model to better handle partial data by @ml-evs in https://github.com/datalab-org/datalab/pull/1501
* Add asynchronous collection export as .eln file (ELNFileFormat) by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1371
* Use item status-style badge for user role in admin dashboard by @ml-evs in https://github.com/datalab-org/datalab/pull/1502
* Add ELN export for items and item graphs by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1389
* Adding version control functionality to all item types (checkpoint, rollback, compare) by @be-smith in https://github.com/datalab-org/datalab/pull/1373
* CI test for plugin builds by @ml-evs in https://github.com/datalab-org/datalab/pull/1510
* Bump preact from 10.26.9 to 10.28.2 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1513
* Fixes for editing groups and creating samples and immediately sharing them by @ml-evs in https://github.com/datalab-org/datalab/pull/1515
* Fix function name in ELN item export by @ml-evs in https://github.com/datalab-org/datalab/pull/1517
* Add item status icon to ItemSelect and search by @ml-evs in https://github.com/datalab-org/datalab/pull/1531
* Update affiliations and about page links by @ml-evs in https://github.com/datalab-org/datalab/pull/1527
* Add formatted group name component by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1533
* Add group icon display in creators column by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1526
* Update copyright year by @ml-evs in https://github.com/datalab-org/datalab/pull/1534
* Add AGENTS.md description of working with the repo by @ml-evs in https://github.com/datalab-org/datalab/pull/1537
* Use slim Python 3.11 base image for API container by @ml-evs in https://github.com/datalab-org/datalab/pull/1538
* API Dockerfile: Run apt clean after installing mdb tools by @ml-evs in https://github.com/datalab-org/datalab/pull/1542
* Fix manager sharing issue by @ml-evs in https://github.com/datalab-org/datalab/pull/1544
* Add file-based suggestions to "add a block" menu and add bottom menu below blocks by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1482
* Unify single item and related item export UI by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1520
* Minor fix preventing duplicate email identities for users by @ml-evs in https://github.com/datalab-org/datalab/pull/1550
* Show locations where present in item select by @ml-evs in https://github.com/datalab-org/datalab/pull/1554
* Redirect non-authenticated users to About page by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1483
* Enable version history UI by @ml-evs in https://github.com/datalab-org/datalab/pull/1546
* Fix mongodump installation issue in server container by @ml-evs in https://github.com/datalab-org/datalab/pull/1561
* Add batch sharing menu option in data table and API by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1525
* Prevent repeated clicks on collection export button by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1549
* Table layout tweaks: partition button groups, increase width and combine table settings by @ml-evs in https://github.com/datalab-org/datalab/pull/1556
* Lock down `/info/stats` endpoint and make about section optional by @ml-evs in https://github.com/datalab-org/datalab/pull/1570
* Add 'sudo' mode for admins that allows them to restrict their admin powers by @ml-evs in https://github.com/datalab-org/datalab/pull/1548
* Add step that looks up any entry references when returning an item by @ml-evs in https://github.com/datalab-org/datalab/pull/1555
* Implement smarter regex search for users and collections by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1474
* Redirect requests for files from the app to the API by @ml-evs in https://github.com/datalab-org/datalab/pull/1589
* Add a column for plotting echem time-series data in hours by @ml-evs in https://github.com/datalab-org/datalab/pull/1596
* Add NMR compatibility with JEOL .jdx files by @isabelcooley in https://github.com/datalab-org/datalab/pull/1532
* Bump webpack from 5.95.0 to 5.105.0 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1587
* Bump markdown-it from 14.1.0 to 14.1.1 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1599
* Bump lodash from 4.17.21 to 4.17.23 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1545
* ELN file format export fixes by @ml-evs in https://github.com/datalab-org/datalab/pull/1600
* Add checksums to `File` for duplicate detection by @ml-evs in https://github.com/datalab-org/datalab/pull/1592
* Remove CODEOWNERS by @ml-evs in https://github.com/datalab-org/datalab/pull/1602
* Add metadata model, support for multiple experiments/nuclei and automatic frequency domain/autophasing in NMR block by @ml-evs in https://github.com/datalab-org/datalab/pull/1598
* Improve error handling for block updates by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1539
* Disable add item buttons when not logged in by @ml-evs in https://github.com/datalab-org/datalab/pull/1586
* Fix `/save-item` to preserve private collections by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1535
* Add support for Battery Data Format (BDF) and multi-file caching in echem block by @be-smith in https://github.com/datalab-org/datalab/pull/1604
* Bump navani v0.1.16 by @be-smith in https://github.com/datalab-org/datalab/pull/1621
* Bump the github-actions group across 1 directory with 3 updates by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1571
* Update dependabot config (trial uv, use dependency groups) by @ml-evs in https://github.com/datalab-org/datalab/pull/1624
* More tweaks for dependabot by @ml-evs in https://github.com/datalab-org/datalab/pull/1632
* Bump the python-production group in /pydatalab with 12 updates by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1635
* Incorporate in situ plugin updates by @ml-evs in https://github.com/datalab-org/datalab/pull/1623
* Fix email auth config behaviour: never auto-activate accounts unless config var is set by @ml-evs in https://github.com/datalab-org/datalab/pull/1645
* Allow blocks to announce multi-file support and use multifile component where supported by @ml-evs in https://github.com/datalab-org/datalab/pull/1647
* Bump pyjwt from 2.11.0 to 2.12.0 in /pydatalab by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1651
* Refactor about page into collapsible sections and add route to customise by @ml-evs in https://github.com/datalab-org/datalab/pull/1652
* Fix item graph rendering by @ml-evs in https://github.com/datalab-org/datalab/pull/1656
* Vendor GSAS-II Bruker raw reader and add Bruker BRML reader by @ml-evs in https://github.com/datalab-org/datalab/pull/1622
* Use BDF parquet files when caching parsed echem by @be-smith in https://github.com/datalab-org/datalab/pull/1663
* Add prototype asynchronous data block processing backend by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1491
* Collected Python updates from dependabot by @ml-evs in https://github.com/datalab-org/datalab/pull/1683
* Bump the github-actions group across 1 directory with 3 updates by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1667
* Echem block: set capacity to null for rest steps for plotting purposes by @be-smith in https://github.com/datalab-org/datalab/pull/1682
* Add preprint to README and CITATION.cff by @ml-evs in https://github.com/datalab-org/datalab/pull/1684
* Compute gravatar hashes server side by @ml-evs in https://github.com/datalab-org/datalab/pull/1686
* EIS block improvements (support for Biologic formats and better plotting) by @be-smith in https://github.com/datalab-org/datalab/pull/1688
* Fix ability to filter by block type in the data table by @ml-evs in https://github.com/datalab-org/datalab/pull/1693
* Migrate admin tables to PrimeVue with bulk operations by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1581
* Return gravatar hashes instead of contact emails from more endpoints by @ml-evs in https://github.com/datalab-org/datalab/pull/1697
* Use SPA navigation between table and edit pages and lazy-load schemas by @ml-evs in https://github.com/datalab-org/datalab/pull/1687
* Add clickable link to QR code renderer by @ml-evs in https://github.com/datalab-org/datalab/pull/1698
* Add sharing API and UI for collections by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1564
* Add collections, supplier and location info to StartingMaterialTable by @be-smith in https://github.com/datalab-org/datalab/pull/1695
* Bump node from 20-bullseye to 22.22-bullseye-slim in /.docker/app by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1633
* Bump the js-production group across 1 directory with 27 updates by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1702
* Bump fast-uri from 3.0.3 to 3.1.2 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1713
* Bump lodash from 4.17.23 to 4.18.1 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1673
* Bump follow-redirects from 1.15.9 to 1.16.0 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1678
* Assorted deps and pre-commit updates by @ml-evs in https://github.com/datalab-org/datalab/pull/1715
* Fix row-click handler in data table and add test by @ml-evs in https://github.com/datalab-org/datalab/pull/1716
* Add cyclic voltammetry (CV) block by @be-smith in https://github.com/datalab-org/datalab/pull/1696
* Bump lodash-es from 4.17.21 to 4.18.1 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1718
* Bump @babel/plugin-transform-modules-systemjs from 7.25.9 to 7.29.4 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1717
* Fix scrolling in '@'-mention dropdown by @ml-evs in https://github.com/datalab-org/datalab/pull/1721
* Hotfix Current units for echem plotting by @ml-evs in https://github.com/datalab-org/datalab/pull/1723
* Add git to app docker build by @ml-evs in https://github.com/datalab-org/datalab/pull/1720
* Bump urllib3 from 2.5.0 to 2.7.0 in /pydatalab by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1724
* Bump mermaid from 11.14.0 to 11.15.0 in /webapp by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1722
* Adding "substance" information to samples by @ml-evs in https://github.com/datalab-org/datalab/pull/1536
* Only install packages older than 1w, and add XPS as core plugin by @ml-evs in https://github.com/datalab-org/datalab/pull/1730
* Downgrade primevue back to 4.1.x by @ml-evs in https://github.com/datalab-org/datalab/pull/1733
* CV/EIS: added error messages for empty files by @be-smith in https://github.com/datalab-org/datalab/pull/1735
* Add datalab-native plugin installer by @ml-evs in https://github.com/datalab-org/datalab/pull/1738
* Add substance information UI component by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1728
* Add draft roadmap and freshen up docs generally by @ml-evs in https://github.com/datalab-org/datalab/pull/1743
* Downsizing bdf.csv and bdf.parquet files by @be-smith in https://github.com/datalab-org/datalab/pull/1729
* Fix for CV block; pass filename to galvani as string by @ml-evs in https://github.com/datalab-org/datalab/pull/1756
* Update echem block to better handle bdf exports and caching by @be-smith in https://github.com/datalab-org/datalab/pull/1760
* Fix SMILES overflow in Substance Information card by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1769
* Add item reference lookup when patching rather than just retrieval by @ml-evs in https://github.com/datalab-org/datalab/pull/1755
* Attempt, once again, to optimise the CI  by @ml-evs in https://github.com/datalab-org/datalab/pull/1736
* Fixing duplication of parthood relationships for cells and samples  by @wuppersaver in https://github.com/datalab-org/datalab/pull/1727
* Add `invoke dev.serve` wrapper to flask run by @ml-evs in https://github.com/datalab-org/datalab/pull/1739
* Add Google and Microsoft OAuth authentication by @DianaAliabieva in https://github.com/datalab-org/datalab/pull/1706
* Fix for dev server unable to load .env by @ml-evs in https://github.com/datalab-org/datalab/pull/1770

## New Contributors
* @isabelcooley made their first contribution in https://github.com/datalab-org/datalab/pull/1532
* @wuppersaver made their first contribution in https://github.com/datalab-org/datalab/pull/1727

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.7...v0.7.0


## v0.6.7 (December 2025)

Another patch release with several UI usability improvements, with highlights including:

- Migration from TinyMCE to TipTap for all free text editors, which features mermaid diagram editing, cross-referencing and markdown support.
- QR codes can now be generated for samples that give public access to sample data to those that scan them.
- Multiple electrochemical cycling files can now be plotted alongside one another in "comparison mode" for the echem block.
- Clicking on the sample table will now open in the current tab by default, with modified click opening in a new tab.
- The media data block now supports SVG files for vector graphics and plots.
- Rule-based chemical formula formatting has been expanded to cover more cases.
- Admins can now assign managers to users through the UI alone, and will now receive email notifications when a user registers, plus users can now verify their contact email addresses via magic links.
- Email authentication no longer requires a global allow list of domains.

### What's Changed

* Migrate from TinyMCE to TipTap by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1349
* Fix modal scrolling for large content by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1446
* Add client-side auth helper for that delays requests until authorised by @ml-evs in https://github.com/datalab-org/datalab/pull/1449
* Add persistent per-item access tokens that can be used in QR codes by @ml-evs in https://github.com/datalab-org/datalab/pull/1220
* Switch access token generating scheme to `secrets.token_urlsafe(16)` by @ml-evs in https://github.com/datalab-org/datalab/pull/1452
* Add support for sanitized SVGs in media block by @ml-evs in https://github.com/datalab-org/datalab/pull/1464
* Reset DataTable page on refresh by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1460
* Enhanced chemical formula formatting by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1445
* Add minimum resizable column width based on header content by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1444
* Added manager to the admin dashboard by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1352
* Unify tooltip styling and add block version display by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1454
* Improvements to email-based authentication and notifications by @ml-evs in https://github.com/datalab-org/datalab/pull/1457
* Add comparison mode for the echem block by @be-smith in https://github.com/datalab-org/datalab/pull/1353
* Allow normal click to open items in same tab from table by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1468


**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.6...v0.6.7

## v0.6.6 (November 2025)

This patch release includes several quality-of-life changes (asynchronous loading of item relationships, filtering by date in the sample table, chemical formula formatting, block plotting improvements), as well as new block options (*in situ* XRD, extensions to FTIR to Shimazdu output files), in preparation for the upcoming 0.7.0 release.

### What's Changed

* Make relationship graph loading asynchronous by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1388
* Add *in situ* XRD block that can handle temperature and electrochemical data by @be-smith in https://github.com/datalab-org/datalab/pull/1287
* Log more informative block errors by @jdbocarsly in https://github.com/datalab-org/datalab/pull/1393
* Server Dockerfile fixes for `arm64` architecture by @DianaAliabieva in https://github.com/datalab-org/datalab/pull/1407
* Clear items before inserting example data to avoid regex search matching a random ID by @ml-evs in https://github.com/datalab-org/datalab/pull/1416
* Add Cypress e2e tests with authenticated user login via magic links by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1379
* Minor improvements to the XRD-insitu block front end by @be-smith in https://github.com/datalab-org/datalab/pull/1412
* Added .csv option to echem block and bumped navani version number by @be-smith in https://github.com/datalab-org/datalab/pull/1397
* Fix dialog boxes font consistency by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1428
* Add calendar date filtering to Datatable by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1422
* Improving formatting of valid chemical formulae by @ml-evs in https://github.com/datalab-org/datalab/pull/1121
* Truncate dialog message when deleting many samples by @ml-evs in https://github.com/datalab-org/datalab/pull/1425
* Constrain which block fields can be set from web requests and saved in db by @ml-evs in https://github.com/datalab-org/datalab/pull/1421
* Update funding/contributor information in README.md by @ml-evs in https://github.com/datalab-org/datalab/pull/1438
* Add Shimazdu file loader for FTIR block by @be-smith in https://github.com/datalab-org/datalab/pull/1413
* Block plotting improvements: ability to hide points, larger plots, external legends by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1263


**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.5...v0.6.6

## v0.6.5 (October 2025)

This patch releases includes several quality-of-life improvements and bug fixes,
including improvements to full-text search, file permissions and the
item relationship graph.

### What's Changed

* Improve regex item search: implict word boundaries, chaining and literal matches by @ml-evs in https://github.com/datalab-org/datalab/pull/1338
* Adjust file permissions so block permission gives equivalent access by @ml-evs in https://github.com/datalab-org/datalab/pull/1376
* Remove name reset in CreateItemModal by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1369
* Item graph display too many items by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1367
* Allow item creation endpoints to use `PUT` by @ml-evs in https://github.com/datalab-org/datalab/pull/1387
* Adding file-size in the filelist by @DianaAliabieva in https://github.com/datalab-org/datalab/pull/1380
* Add support for PSTrace EIS output txt files by @ml-evs in https://github.com/datalab-org/datalab/pull/1383
* Fix collection creation modal error display for duplicate IDs by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1382

### New Contributors

* @DianaAliabieva made their first contribution in https://github.com/datalab-org/datalab/pull/1380

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.4...v0.6.5

## v0.6.4 (September 2025)

This patch release simply fixes a few UI bugs introduced in v0.6.3 (and earlier).
It also signifies the adoption of the Contributor Covenant Code of Conduct (v2).

### What's Changed

* Broken admin dashboard UI for user management by @ml-evs in https://github.com/datalab-org/datalab/pull/1361
* Inability to insert new items created via copying into a collection by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1356
* Long message dialog box formatting by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1346

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.3...v0.6.4

## v0.6.3 (September 2025)

This patch release primarily improves block serialization performance and extensibility, as well as improving error handling for both developers and users.

> [!WARNING]
> This release hardens the `SECRET_KEY` configuration to enforce setting a custom key with a minimum entropy; old keys may need to be rotated.

### What's Changed

* Major refactoring of block life cycle, with better possibilities for validation of block data before and after saving by @ml-evs in https://github.com/datalab-org/datalab/pull/1311
* Replace browser-native dialogs with custom datalab dialog service by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1212
* Resolve CVEs on mermaid.js and cross-spawn by @dependabot[bot] in https://github.com/datalab-org/datalab/pull/1317
* Hardened `SECRET_KEY` configuration by @ml-evs in https://github.com/datalab-org/datalab/pull/1324
* Improve performance and memory utilisation when serialising blocks by @ml-evs in https://github.com/datalab-org/datalab/pull/1329
* Improve performance of XRD block file reader by @ml-evs in https://github.com/datalab-org/datalab/pull/1331
* Enable electrochemistry block to read multiple files and stitch them together by @be-smith in https://github.com/datalab-org/datalab/pull/1307
* Fix issue with chat block rendering introduced in v0.6.2 by @ml-evs in https://github.com/datalab-org/datalab/pull/1340.
* Fix case sensitivity of TIF file handling in media block by @ml-evs in https://github.com/datalab-org/datalab/pull/1326.

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.2...v0.6.3

## v0.6.2 (August 2025)

This patch release adds a hotfix for broken media blocks when encoding TIF files (https://github.com/datalab-org/datalab/pull/1318).

#### What's Changed

* Fix serialisation of block data with nested file IDs in data model by @ml-evs in https://github.com/datalab-org/datalab/pull/1319

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.1...v0.6.2

## v0.6.1 (August 2025)

This patch release adds an API config option `CONFIG.ROOT_PATH` to allow
deployments to easily serve the API under a subpath (e.g., `\api`) on the
same subdomain as the app.
It also features a new validation model for block data, which should currently
have no user-facing effects, but will allow for more formal extensions of block
schemas in the future.

### What's Changed
* Add `DataBlockResponse` model to sanitize `blocks_obj` in API by @ml-evs in https://github.com/datalab-org/datalab/pull/1310
* Add `CONFIG.ROOT_PATH` option to deploy API from custom path by @ml-evs in https://github.com/datalab-org/datalab/pull/1315

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.6.0...v0.6.1

## v0.6.0 (August 2025)

This release includes significant new functionality and UI redesign, a  
fledgling plugin ecosystem, as well as several bug and quality-of-life
fixes, performance improvements and backwards-compatible API enhancements.

> [!WARNING]
> This release also bumps the supported MongoDB version all the way from v3 to v8. Whilst older MongoDB versions should still continue to work, version 8 will now be tested and used in the docker builds, so we recommend you upgrade. For existing databases this requires you to first dump the database using `mongodump` with the old MongoDB version, then upgrade to the new version and restore the database with `mongorestore`. If you unsure about this process then please ask us for help!

### Highlights

- Extra functionality for all data tables: column selection, persistent user
  preferences and improved filtering.
- Improved inventory management: native UI for hazard labels, CAS numbers and external barcodes,
  complementing the first release of the
  [`datalab-cheminventory-plugin`](https://github.com/datalab-industries/datalab-cheminventory-plugin)
  for two-way sync with [cheminventory.net](https://cheminventory.net).
- Starting materials can now also have synthesis information recorded for them.
- New blocks for UV-Vis data and *in situ* NMR data (developed in separate core
  plugin at
  [`datalab-app-plugin-insitu`](https://github.com/datalab-org/datalab-app-plugin-insitu)),
  as well as new file formats supported in the XRD (Rigaku's .rasx, variants of .xy), NMR (JCAMP-DX) blocks
  and media block (PDF documents).
- A fledgling plugin ecosystem with ways to easily add new blocks to a specific
  *datalab* instance ([docs](https://docs.datalab-org.io/en/v0.6.0/plugins/)), with [`datalab-server`](https://pypi.org/project/datalab-server) PyPI package for easier dependency management.
- Improved item search throughout the API, removing the need to search on
  whitespace or punctuation delimited words (e.g., ID matches will now begin after
  just 3 characters, rather than needing to type a full ID).
- More powerful UI block interactions via "events" that can be written purely Python ([docs](https://docs.datalab-org.io/en/v0.6.0/blocks/)).

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.5.2...v0.6.0

## v0.5.2 (March 2025)

This patch release makes several visual/interactivity improvements around
loading states in the UI, and adds two new blocks: FTIR and a tabular data
block for plotting data from within generic CSV/Excel files.

### What's Changed
* Fix docs link in mkdocs by @ml-evs in https://github.com/datalab-org/datalab/pull/1044
* Improve loading state for data-intensive blocks by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/1049
* Add support for reading excel-like spreadsheets in tabular data block by @ml-evs in https://github.com/datalab-org/datalab/pull/1052
* Add Login Splash Screen by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/907
* Added FTIR block and associated tests by @be-smith in https://github.com/datalab-org/datalab/pull/1061
* Update CITATION.cff by @ml-evs in https://github.com/datalab-org/datalab/pull/1069

### New Contributors
* @be-smith made their first contribution in https://github.com/datalab-org/datalab/pull/1061

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.5.1...v0.5.2

## v0.5.1 (January 2025)

This patch release simply pins the `uv` version used in builds to avoid future breakages.

### What's Changed

* Bump the github-actions group across 1 directory with 2 updates by @dependabot in https://github.com/datalab-org/datalab/pull/1031
* Update uv to 0.5.x now that dynamic versioning is supported by @ml-evs in https://github.com/datalab-org/datalab/pull/1032
* Pin uv by @ml-evs in https://github.com/datalab-org/datalab/pull/1039

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.5.0...v0.5.1

## v0.5.0 (December 2024)

This release is long overdue following the 8 pre-releases. The 0.5.x series now provides a stable base for us to begin some major overhauling of how we handle custom schemas and data blocks, both of which will form the basis of 0.6.x in the new year.

The Ansible playbooks at [datalab-ansible-terraform](https://github.com/datalab-industries/datalab-ansible-terraform) and the Python API package at [datalab-api](https://github.com/datalab-org/datalab-api) already both support this release.

Many thanks to all contributors: developers, user feedback and deployment managers!

### Breaking changes

* The Python server has been entirely repackaged with `uv` for much more streamlined dependency management (especially for external plugins). If you are using the docker deployments, then nothing should change for you, but developers may need to adjust their development setups following the [installation instructions](./INSTALL.md).

### Highlights

* The table component used to display all items has been entirely rewritten, and is now more visually responsive and can accommodate custom schemas/components.
* QR code generation and scanning for all items, optionally using the new [datalab pURL service](https://purl.datalab-org.io/) when configured with `VUE_APP_QR_CODE_RESOLVER_URL`.
* Following from the block info from the last release, the API now reports the schemas it is using at `/info/types`, ready for these to become more easily configurable at the deployment level. The edit page and item table are beginning to dynamically use this information.
* Improvements to the collections UI, allowing items to be added to collections more easily after creation.
* Ability to selectively share items with certain users; this will soon be expanded to user groups and projects (via collections) with configurable defaults.
* Several bug fixes to the UI, API (timezone consistency, tweaks to the LLM integration, better handling of permissions edge cases)
* Ease-of-use features and new configuration options for deployments.


**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.4.4...v0.5.0


## v0.4.4 (August 2024)

This release primarily contains some bugfixes for the echem block, as well as tidying in preparation of the next release.

### What's Changed

* Removed unused css by @BenjaminCharmes in https://github.com/datalab-org/datalab/pull/826
* Remove final mentions of odbx.science by @ml-evs in https://github.com/datalab-org/datalab/pull/827
* Add routes for resolving items by refcode by @ml-evs in https://github.com/datalab-org/datalab/pull/807
* Fix block errors caused by seemingly defunct theme options in bokeh  by @ml-evs in https://github.com/datalab-org/datalab/pull/829
* Update to latest navani version, fixing Neware normalisation issues by @ml-evs in https://github.com/datalab-org/datalab/pull/836
* Reload echem data by default, unless disabled by @ml-evs in https://github.com/datalab-org/datalab/pull/840


**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.4.3...v0.4.4


## v0.4.3 (July 2024)

This release simply re-enables Firefox testing in the CI, and reorganises the associated cloud runs.

### What's Changed
* Re-enable Firefox e2e tests by @ml-evs in https://github.com/datalab-org/datalab/pull/711

**Full Changelog**: https://github.com/datalab-org/datalab/compare/v0.4.2...v0.4.3


## v0.4.2 (July 2024)

This release adds an update to the batch item creation UI to include other item types, and includes a new preview of the tabular UI which can be accessed at the path `/next`, as well as several UI tweaks and fixes.

### What's Changed

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

### What's Changed

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
