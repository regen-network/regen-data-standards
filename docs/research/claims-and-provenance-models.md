# Claims and provenance models: recommendations for WP1-01

Research synthesis, revised 23 September 2026. Supports [WP1-01 / #67](https://github.com/regen-network/regen-data-standards/issues/67).
**Recommendations for subsequent ADRs, not adopted schema decisions.**

**Reuse existing ontologies where their meaning fits.** Use PROV-O for production history and revisions; retain `rfs:hasClaimant` as a proposed specialization of PROV attribution. Define Claim content and review requirements ourselves: provenance vocabulary alone does not supply them.

## Sources at a glance

| Source | Proposed model or contribution | Relevance to our engine |
| --- | --- | --- |
| Massari et al., [Representing provenance and track changes of cultural heritage metadata in RDF][SURVEY] (online 2025; issue 2026) | Compares statement annotations, graph packages and version histories. | Helps choose representation; does not propose a Claim ontology. |
| Sahoo et al. (2010), [Provenance Context Entity (PaCE): Scalable Provenance Tracking for Scientific RDF Data][PACE] | Encodes source context in identifiers of statement components. | Preserve source distinctions; avoid adopting its identifier scheme. |
| [Nanopublication Guidelines][NANO] | Separates assertion, provenance and publication metadata into named graphs. | Reuse the separation; packaging remains optional. |
| W3C [PROV-O][PROV] (2013) | Describes entities, activities, responsible agents and production history. | Main vocabulary to reuse; specialize attribution for claimant. |
| Clark, Ciccarese and Goble (2014), [Micropublications][MICRO] | Organizes claims, supporting data/methods and challenges as arguments. | Distinguish evidence judgments from production history. |
| [FAIRSCAPE][FAIRSCAPE] (online 2021; issue 2022) and [EVI][EVI] | Records reproducible computations and evidence relationships. | Useful when a workflow needs computational evidence. |
| [SSN/SOSA Recommendation][SOSA] (2017) | Describes observations, properties, methods, results and times. | Reuse within ecological measurement Claims. |
| Kuhn and Dumontier (2014), [Trusty URIs][TRUSTY] | Embeds verifiable content hashes in identifiers, including RDF packages. | Informs hashing requirements; identifier format is a separate choice. |
| Naja and Gibbins (2018), [Using Provenance to Efficiently Propagate SPARQL Updates on RDF Source Graphs][RGPROV] | Tracks dependencies to update derived results when sources change. | Relevant to derived queries, not claimant or review semantics. |

## 1. Questions these sources help answer

The main question is **which existing terms should our schemas reuse, and which meanings must we define?** An ontology defines meanings and relationships; a validation schema specifies required and allowed fields.

| Design question | Recommended direction |
| --- | --- |
| What constitutes a Claim, and who is its claimant? | Define the related statements asserted together; retain `rfs:hasClaimant` as a proposed specialization of PROV attribution (§3.1). |
| Asserted content versus provenance? | Attribution and author-cited sources can be Claim content; extraction, submission and later review have separate records. |
| Evidence and attestation? | Distinguish citation, derivation and an attributed judgment of support, challenge or approval. |
| Schema composition? | Combine shared Claim definitions with selected PROV and domain terms, then specify validation constraints. |
| Identity and versioning? | Use PROV for genuine revisions; decide content hashing separately. |

**Example conventions:** RDF statements are subject–relationship–object triples; a graph groups triples. An IRI is an identifier, often a web address; `_:claim` is a local node without a global identifier. Examples are hypothetical, omit prefix declarations and use `ex:` for illustrative terms. **Source** describes the cited work; **assessment** gives our interpretation and recommendation.

## 2. Comparison of the sources

Each assessment below explains the source, gives an example and identifies what we could reuse and its limits. The five design questions are answered across sources in §3.

### 2.1 Massari survey: where to attach provenance

**Source.** The survey compares provenance attached to individual statements, groups and historical descriptions. Table 1 distinguishes production history, justification and uses of provenance to assess trust; Table 4 compares representation capabilities ([§§2–5][SURVEY]). Its OpenCitations example preserves earlier descriptions with attribution and change history: description-v2 links to description-v1 ([§4, Fig. 3][SURVEY]).

**Example:** attribute an area statement to Alice, or attribute a package containing area, period and method to Alice. The first identifies who supplied a field; the second identifies who stands behind the package.

**Assessment.** Separate Claim meaning, statement grouping and provenance vocabulary. PROV-O supplies relationship meanings; named graphs or statement records organize data. Start with related statements grouped in a Claim; introduce field-level records when evidence or review needs them. The survey cannot select our boundaries or approval rules, and its summaries need checking against primary sources (see PaCE below). Reuse the historical-description pattern without assuming a hash scheme.

### 2.2 PaCE: preserve each statement's source context

**Source.** PaCE distinguishes otherwise identical statements by incorporating provenance context into component identifiers. Context may describe a document or sensor, location and time. It uses Provenir for data, agents and processes. Figure 2 compares contextualizing one, two or all three triple components; §2.3 supplies inference rules and §3 benchmarks storage and queries ([§§2.1, 2.3, 3][PACE]).

**Adapted example:** two reports agree on the plot's area but retain separate source identifiers.

```turtle
<https://example.org/reportA/plotA> ex:areaHa 12 ; provenir:derives_from ex:reportA .
<https://example.org/reportB/plotA> ex:areaHa 12 ; provenir:derives_from ex:reportB .
```

**Assessment.** Preserve both sources so one can be challenged independently. Prefer shared plot identifiers and separate attributed Claims: contextual plot identifiers complicate entity lookup. Additional inference rules and biomedical benchmarks do not establish benefits for our workload. The survey's “primary sources only” characterization is too narrow; PaCE also discusses sensor context and confidence. **Reuse the source distinction, not the encoding.**

### 2.3 Nanopublications: separate assertion from publication

**Source.** A nanopublication packages a small assertion in four named graphs: assertion, its provenance, publication information and links joining them. A named graph is a group of triples with an identifier ([“Basic Elements” and “Formal Structure”][NANO]).

**Example:** the assertion describes plot A's 12 ha area; provenance attributes it to Cooperative A and cites a report; publication information identifies the organization distributing the dataset.

**Assessment.** Reuse these distinctions, but begin with one Claim graph and separate service/review records. Require four-graph packaging only for a demonstrated publication or query need. Graph boundaries alone establish neither endorsement nor hash coverage.

### 2.4 PROV-O: production history and responsibility

**Source.** PROV distinguishes entities (such as documents), activities (such as extraction) and agents (people, organizations or software). `wasAttributedTo` identifies an entity's responsible agent; `wasGeneratedBy` links an output to its producing activity. Attribution is broader than “made this assertion” ([PROV-O §§3.1–3.3][PROV]; [PROV-DM §§5.1–5.3][PROVDM]).

**Example:** extraction7 uses report-v1, generates draft-v1 and is associated with tool T; the draft is subsequently asserted by Cooperative A.

**Assessment.** Reuse PROV for derivation, activity inputs/outputs and genuine revisions. Specialize attribution for claimant only after defining responsibility for the assertion. PROV supplies neither our Claim boundary nor criteria for truth, approval or required fields.

### 2.5 Micropublications: evidence as an attributed argument

**Source.** A micropublication organizes a principal claim, supporting data/methods/statements and challenges. Support is transitive; challenges can be indirect. It distinguishes explicit challenges from disagreements inferred by third parties ([“Logical formalization,” Figs. 3–4; Examples 2, 8][MICRO]).

**Example:** samples support an area estimate; a reviewer challenges the sampling method rather than the number.

**Assessment.** Citation means “referenced”; derivation means “used to produce”; support means “offered by someone as a reason to believe.” Record who makes that judgment. Do not import transitive support or automatic rejection of dependent Claims as review policy.

### 2.6 FAIRSCAPE/EVI: evidence from reproducible computation

**Source.** FAIRSCAPE records datasets, software and computations. Its Evidence Graph Ontology (EVI) extends PROV with evidence relationships ([“Enabling Transparency through EVI's Formal Model”][FAIRSCAPE]; [repository “A worked example”][EVI]).

**Example:** computation7 uses samples-v1 and model-v2 to generate estimate-v1; a Claim cites that estimate.

**Assessment.** Start with PROV input/output history. Evaluate EVI when a selected workflow needs richer computational evidence; neither its formal model nor its service architecture is a base requirement. Challenged inputs should trigger reassessment, not silently rewrite authored Claims.

### 2.7 SOSA: reuse ecological observation terms

**Source.** SOSA describes an observation's feature of interest, measured property, procedure and result. It distinguishes when the result applies from when the observation completed ([2017 Recommendation §§4.3–4.8][SOSA]).

```turtle
ex:obs1 a sosa:Observation ;
    sosa:hasFeatureOfInterest ex:plotA ;
    sosa:observedProperty ex:soilCarbonConcentration ;
    sosa:usedProcedure ex:methodV1 ;
    sosa:hasResult ex:result1 .
```

**Assessment.** Reuse these terms within domain Claims, with claimant attribution separately. SOSA supplies neither carbon eligibility rules nor reviewer authority or Claim identity. Add result value/unit and workflow constraints before using this example as a domain fixture.

### 2.8 Trusty URIs: specify the entire hashing procedure

**Source.** Trusty URIs embed content hashes. FA hashes file bytes; RA handles RDF datasets, named graphs, blank nodes and self-reference. Self-reference uses a temporary placeholder ([§3, “Self-References,” “Blank Nodes,” “Modules”][TRUSTY]).

**Example:** `resource.<placeholder> → normalized RDF → hash → resource.RA<digest>`.

**Assessment.** Reuse independently verifiable hashing rules, not the format by default. Prefer Regen Ledger Graph identifiers if they cover the chosen content. Hashes establish integrity, not truth, authorship or availability. Trusty URI normalization and RDF Dataset Canonicalization are not interchangeable.

### 2.9 RGPROV: maintain derived query results

**Source.** RGPROV tracks source graphs and operations to propagate additions/deletions into derived results ([§4, Figs. 3–6; §5][RGPROV]). **Example:** if A and B both supply an area statement, deleting it from B must not remove it from their combined result while A still supplies it.

**Assessment.** Track input versions and calculations to identify results needing reassessment. Defer RGPROV vocabulary/algorithms from the base schema: §3 excludes blank nodes and several SPARQL features; §5.3 restricts inference; §6 evaluates small graphs. Its lesson fits WP4/WP5 query maintenance; updating a query result is different from revising an author's Claim.

### 2.10 Supporting vocabularies, formats and schema tools

| Approach | Model and example | Assessment |
| --- | --- | --- |
| [Schema.org Claim][SCHEMA] / [ClaimReview](https://schema.org/ClaimReview) | Web claim/fact-check descriptions: text, author, publication appearance, rating. | Optional export; inadequate for our core evidence, immutable-content and validation requirements. |
| [Wikibase / CIDOC CRM E13, survey §3][SURVEY] | Statement or property-assignment records with qualifiers, source and actor: Alice assigns plot A an area. | Useful field-attribution pattern; no need to adopt platform-specific structures. |
| [RDF 1.2 triple terms §1.5][RDF12] | Refers to a triple without asserting it: “Alice said plot A is 12 ha.” | Useful quotation model; defer until our parsers, validators and hashing support it. |
| [Verifiable Credentials 2.0 §§3.1–3.3][VC] | Digitally verifiable issuer statements: V signs a credential about C1. | Possible exchange/proof mechanism; does not establish truth or define review meaning. |
| [in-toto Statement v1, “Schema” / “Fields”][INTOTO] | JSON attestation identifies subject by digest and assertion type: review of file H. | Reuse explicit signed targets; export only for a concrete consumer. |
| [Dublin Core Terms, `references`][DCT] | Describes a resource's citation of another: Claim C1 references report R-v1. | Reuse for citations; it does not mean derivation or endorsement. |
| [RDF Schema §3.5][RDFS] | Defines property specialization: a claimant link can imply a broader attribution link. | Reuse `subPropertyOf`; implication is one-way and requires inference or query expansion. |
| [LinkML URI mappings][LINKML] | Connects schema fields to RDF properties: `slot_uri: rfs:hasClaimant`. | Reuse our schema tooling; mapping metadata alone does not establish equivalent meanings or matching JSON/RDF validation rules. |
| [RDF Dataset Canonicalization][CANON] | Produces a standard serialization, including consistent blank-node labels, for hashing. | Relevant to identity; does not make all statements with the same real-world meaning identical. |

## 3. Recommendations by design question

### 3.1 What constitutes a Claim, and who asserts it?

**Our recommendation, drawing on the survey, nanopublications and PROV:** a Claim records related statements an identified claimant presents together. A measurement may need subject, value, unit and context across several triples. PROV describes its history but does not define which statements form one Claim. Require neither ecological impact nor independent approval of every generic Claim; a later review is a separate assertion.

Our [existing `hasClaimant`][CLAIM] identifies the individual, organization or community making the claim. A project's operator, data extractor and publisher may be different actors; these are workflow roles, potentially performed by the same actor.

| Option | Benefit and limitation | Recommendation |
| --- | --- | --- |
| Use `prov:wasAttributedTo` directly | Standard property, but does not distinguish assertors from other contributors. | Viable only if its use on Claims is explicitly restricted to claimants. |
| Specialize it with `rfs:hasClaimant` | Precise meaning plus PROV compatibility; generic queries need the property hierarchy or an expanded view. | **Preferred.** |
| Model an assertion activity with qualified agent roles | Rich participation history, but more records/joins; claimant still needs defining. | Add when a workflow needs this detail. |
| Keep an unrelated custom claimant property | Simple locally, but other systems need a separate provenance mapping. | No advantage over specialization. |

**Proposed meaning:** Claim is an assertion record; claimant identifies who takes responsibility for making that assertion. This makes claimant a narrower attribution relation, **if [ADR 0001: Claim RDF shape and provenance boundaries][ADR] accepts that definition**, especially for imports whose original authors did not produce the RDF.

```turtle
# Proposed vocabulary, followed by a hypothetical instance.
rfs:Claim rdfs:subClassOf prov:Entity .
rfs:hasClaimant rdfs:subPropertyOf prov:wasAttributedTo .
_:claim a rfs:Claim ;
    rfs:hasClaimant ex:cooperativeA ;
    rfs:hasSubject ex:plotA .
```

Under [RDF Schema §3.5][RDFS], every claimant link then implies attribution; the reverse does not follow. A query engine must apply that relationship or expose implied triples separately. Do not silently add inferred statements to hashed content, or declare the properties equivalent.

**Import distinction:** “Alice asserted X” differs from “our extractor reports that Alice asserted X.” Generating RDF does not make the extractor the claimant of X.

### 3.2 Asserted content versus provenance

**Our recommendation, drawing on nanopublications and PROV:** distinguish the claimant's assertion from processing and publication history. Attribution and author-cited sources can belong in Claim content; not every provenance fact needs to be hashed with it.

| Record | Example and recommended placement |
| --- | --- |
| Authored assertion | Cooperative A asserts an area and cites report R-v1: Claim content, including attribution and selected evidence references. |
| Extraction history | Tool T-v2 extracted page 3: processing record; include in Claim content only if the author asserts it. |
| Submission history | Attempts 42 and 43 submit C1: service records pointing to unchanged C1. |
| Review | B approves C1's area under rule R-v2: separate judgment targeting that version and field. |
| Current status | C2 is preferred or a review revoked: maintained status/history outside immutable C1. |

**Submission links inside a Claim** are possible if the identifier is allocated beforehand; a Claim can also cite an earlier receipt as evidence. But changing an attempt link inside hashed content changes the Claim ID. When the same Claim is submitted again, record a new submission attempt referencing the unchanged Claim identifier. A hashing cycle occurs only when both content-derived identifiers depend on each other.

**Workflow to test:** read a versioned report → extract candidate → confirm content and claimant → submit → record validation and acceptance/rejection. Human authoring skips extraction. Define a portable submission schema only for a named consumer's need; OutputRecord is not the design basis.

**Operator: distinguish the assertion from the claimed outcome.** The current [Claim schema][CLAIM] uses `hasOperator` for the agent responsible for operations producing the outcome. PROV assigns responsibility for an activity through `prov:wasAssociatedWith`; `prov:wasAttributedTo` attributes an entity to an agent ([PROV-DM §§5.3.2–5.3.3][PROVDM]). For example, NGO A asserts that Cooperative B restored a wetland: A is the claimant; B is associated with the restoration activity. If the resulting wetland state is modeled as an entity, it can be attributed to B. Attributing the Claim itself to B would express a different responsibility.

**Our recommendation:** describe the operator on the relevant domain activity, allowing several operations and participants. Retain a Claim-level shortcut only for a demonstrated workflow need; do not directly map the current `hasOperator` to PROV attribution. Keep operator responsibility explicit even when operator and claimant coincide. The activity description can remain within the Claim's asserted, hashed content; using a linked node does not settle that boundary. Placement and any shortcut remain schema ADR questions.

### 3.3 Evidence and attestation relationships

**Our recommendation, drawing on micropublications, FAIRSCAPE/EVI and PROV:** distinguish citations, actual derivation and an attributed judgment of support or challenge. Use PROV for computation history; use richer argument relationships only when a workflow needs them. A challenge should trigger reassessment, not automatic rejection of dependent Claims.

Extend the existing [Attestation][ATTEST] where needed to identify **reviewer, target Claim version, reviewed fields, rule/method version, verdict, rationale and evidence**. Resolve its missing scope/version semantics before adopting a whole argument ontology. Whether it is a Claim subtype remains open.

### 3.4 Schema composition: select terms, then define constraints

**Our recommendation, drawing on PROV, SOSA and LinkML:** combine shared Claim/actor definitions with relevant observation and evidence terms. Link observations, results and claimants rather than copying every external field onto Claim.

In [LinkML][LINKML], `slot_uri` selects the emitted RDF property. Keeping `slot_uri: rfs:hasClaimant` plus a PROV subproperty declaration differs from emitting `prov:wasAttributedTo` directly. Descriptive mapping metadata does not substitute for that RDF relationship.

**Recommendation:** publish vocabulary relationships alongside validation schemas; check generated RDF and queries. Pin schema imports and specify which class validation starts from: importing a module does not make every record conform to it. Verify that generated JSON Schema (JSON) and SHACL (RDF) enforce the intended rules.

| Meaning | Recommended term or action |
| --- | --- |
| Responsible person, organization or software | Reuse `prov:Agent` and relevant subtypes. A collective agent does not make every member a co-claimant. |
| Record produced from a source | `prov:wasDerivedFrom` for actual derivation, not every citation or supporting document. |
| Cited document | `dcterms:references`; add page/fragment and evidence version when needed. Citation alone does not assert support. |
| Activity inputs and outputs | `prov:used` and `prov:wasGeneratedBy` for extraction/calculation history, not endorsement. |
| Genuine revision | `prov:wasRevisionOf`; maintain which version an application currently accepts separately. |
| Assertion time | Define explicitly; do not substitute import, file-generation, publication or observation time. A modeled assertion activity could use PROV events. |
| Claim subject | Retain `hasSubject`; attribution identifies responsibility, not what a Claim is about. |
| Operator responsible for the claimed operations | Prefer `prov:wasAssociatedWith` on the domain activity; decide whether a Claim-level shortcut is needed (§3.2). |
| Support, challenge or approval | Specify reviewer, target version, scope and verdict (§3.3); derivation does not express these judgments. |

Sources: [PROV-O §§3.1–3.3][PROV], [PROV-DM §§5.1–5.3][PROVDM], [Dublin Core `references`][DCT], existing [Claim][CLAIM] and [Attestation][ATTEST]. Reusing terms does not require importing an entire ontology into each instance, and supplies neither mandatory fields nor business rules.

### 3.5 Identity and versioning

**Our recommendation, drawing on PROV, Trusty URIs and the survey:** keep immutable versions linked by `prov:wasRevisionOf` for genuine revisions. This does not confer authority, select a current version or inherit approval. The identity ADR must define hashed statements, schema declarations, normalization, digest and IRI format. Including a record's own digest requires explicit exclusion/replacement during hashing.

OpenCitations snapshots preserve historical descriptions (§2.1); JC's “Snapshot” is a collection of Claim identifiers. Keep those meanings distinct. RGPROV informs changes to derived query results, not automatic rewriting of authored Claims.

## 4. Critical assessment of our current direction

| Inspected design input | Recommendation or unresolved problem |
| --- | --- |
| [Claim][CLAIM] requires claimant and ecological impact; includes changing verification status and its hash/IRI. | Keep claimant; move domain-only requirements into extensions and changing status outside immutable content. Publish proposed PROV alignment. |
| Existing `supersedes` | Separate genuine revision from selection of the current version. Only the first maps to PROV revision. |
| JC's [domain model][JC] separates content, judgments and service observations. | Useful proposal; service history still counts as provenance. |
| JC permits missing claimant and deferred validation. | Do not adopt as MVP defaults: these conflict with the planned attributed, validated workflow. |
| JC's [spike][SPIKE] hashes canonical RDF plus separately encoded schema identifiers ([code][IDENTITY]). | Prototype choice; decide whether schema declarations are authored content or service-selected validation metadata. |
| Spike [projection][PROJECTION] discards graph names. | Cannot preserve nanopublications unchanged; retain boundaries or reject unsupported multi-graph input. |
| Spike uses blank-root examples and handwritten validation artifacts. | Neither establishes a required root pattern nor a generated validation pipeline. Admission does not require a blank root. |

## 5. ADR handoff: decisions still needed

**Schema/provenance:** take the vocabulary recommendations in §3 to [ADR 0001: Claim RDF shape and provenance boundaries][ADR] ([WP1-04 / #70](https://github.com/regen-network/regen-data-standards/issues/70)). Resolve:

1. Does claimant always mean responsibility for making the assertion, including imports and collectives? Confirm before declaring the PROV subproperty.
2. What does assertion time mean, including unknown times and repeated assertion occasions?
3. Which statements and linked descriptions form one Claim? Start with one graph unless a demonstrated need requires multiple graphs.
4. Which evidence links need more than citation/derivation? Who asserts support/challenge, over which fields and rule version?
5. Is Attestation a Claim subtype or a separate type sharing assertion fields? Which domain requirements remain after vocabulary reuse?
6. Should operator responsibility be recorded on domain activities, and does any workflow justify retaining `hasOperator` on Claim? Define the scope and content boundary (§3.2).

**Service identity ([WP1-08](https://github.com/regen-network/claims/issues/1)):** decide exact hashed content, schema declarations, canonicalization, digest/IRI format, self-reference and handling of revisions/repeated submissions. Ontology reuse does not settle these.

**Proposed checks:** two claimants assert the same measurement; a tool extracts a draft another actor asserts; a reviewer challenges one field. Show claimant, provenance and review query results for each. These are proposed fixtures, not executed tests. Agreed schemas then feed [WP1-05](https://github.com/regen-network/regen-data-standards/issues/71) and [WP1-06](https://github.com/regen-network/regen-data-standards/issues/73).

## Source and inspection notes

PaCE/RGPROV section citations refer to linked author manuscripts. The [SOSA paper][SOSAPAPER] was screened through its abstract; detailed analysis uses the W3C Recommendation. Repository tools were inspected, not installed or benchmarked; cited project revisions remain design inputs, not assumed merged decisions. Ecological rules and acceptable evidence need workflow research.

Historical inspection only: [OutputRecord PR #55](https://github.com/regen-network/regen-data-standards/pull/55), [schema][OUTPUT] and [contract][OUTPUT-CONTRACT] at `a0f7371`.

[CLAIM]: https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml
[ATTEST]: https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Attestation.yaml
[OUTPUT]: https://github.com/regen-network/regen-data-standards/blob/a0f73711d3845f0f472b0276c8bb137967fcf1fd/schema/src/OutputRecord.yaml
[OUTPUT-CONTRACT]: https://github.com/regen-network/regen-data-standards/blob/a0f73711d3845f0f472b0276c8bb137967fcf1fd/docs/output-record-contract.md
[ADR]: https://github.com/regen-network/regen-data-standards/blob/3f2bf5d9b20f1bc583aef4bd2fc7484576e94191/docs/adr/0001-claim-substance-canonicalization.md
[JC]: https://github.com/ybird-labs/claims/blob/217fafdd9685fb427ed74f440f9fa65a475f4885/design/CLAIMS_ENGINE_DOMAIN_MODEL.md
[SPIKE]: https://github.com/ybird-labs/claims/blob/217fafdd9685fb427ed74f440f9fa65a475f4885/spike/README.md
[IDENTITY]: https://github.com/ybird-labs/claims/blob/217fafdd9685fb427ed74f440f9fa65a475f4885/spike/src/identity.rs
[PROJECTION]: https://github.com/ybird-labs/claims/blob/217fafdd9685fb427ed74f440f9fa65a475f4885/spike/src/projection.rs#L81-L90
[MICRO]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4530550/
[TRUSTY]: https://arxiv.org/html/1401.5775
[FAIRSCAPE]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8760356/
[EVI]: https://github.com/fairscape/EVI
[SOSA]: https://www.w3.org/TR/2017/REC-vocab-ssn-20171019/
[PACE]: https://lhncbc.nlm.nih.gov/LHC-publications/PDF/pub2010012.pdf
[SURVEY]: https://doi.org/10.1093/llc/fqaf076
[RGPROV]: https://eprints.soton.ac.uk/421525/1/ImanNajaPaper18.pdf
[PROV]: https://www.w3.org/TR/prov-o/
[PROVDM]: https://www.w3.org/TR/prov-dm/
[NANO]: https://nanopub.net/guidelines/working_draft/
[RDFS]: https://www.w3.org/TR/rdf-schema/#ch_subpropertyof
[DCT]: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/
[SOSAPAPER]: https://arxiv.org/abs/1805.09979
[SCHEMA]: https://schema.org/Claim
[RDF12]: https://www.w3.org/TR/2026/CR-rdf12-concepts-20260407/
[VC]: https://www.w3.org/TR/vc-data-model-2.0/#core-data-model
[INTOTO]: https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md
[LINKML]: https://linkml.io/linkml/schemas/uris-and-mappings.html
[CANON]: https://www.w3.org/TR/rdf-canon/
