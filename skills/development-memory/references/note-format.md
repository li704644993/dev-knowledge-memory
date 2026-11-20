# Development Note Format

Keep one canonical note per topic. Include enough evidence for the next agent to locate the correct behavior without pretending to encode the whole repository.

## Metadata

Pass metadata to Basic Memory `write_note`/`edit_note`. Basic Memory manages title, type, permalink and tags; preserve its returned permalink.

```yaml
aliases: [human vocabulary, technical identifier]
repositories: [owner/repository]
status: implemented-unverified
created: YYYY-MM-DD
last_checked: YYYY-MM-DD
source_agent: Codex
publish: false
code_revisions:
  owner/repository: actual-checked-revision
verification_scope: What was actually read or executed
deployment_status: Not deployed or not checked
```

These are authoring placeholders, not claims to paste unchanged. Omit inapplicable optional fields. If a source has uncommitted changes, label the observation as a working-tree result, not as a fact guaranteed by HEAD.

## Body

- Search terms: domain aliases, versions, models, tables, interfaces and commands that users actually mention.
- Scope and evidence status: which feature/version this describes and what remains unverified.
- Mechanism: important relationships, ID meanings, entry points and order of side effects.
- Decisions: rationale evidenced by the task, code/comments or linked decisions; unknown motivation stays unknown.
- Constraints and pitfalls: material mistakes the note should prevent, without turning a one-off workaround into a universal rule.
- Sources: repository-relative paths plus symbols and revisions; link an authoritative issue or PR when one was actually checked. Local-only paths are labeled as such.
- Relations: links to relevant concepts/topics within the development directory.

For imported documentation, preserve its original location/date when known, mark the imported status, and separate source claims from newly verified behavior. Do not present an old incident as an active defect without checking the present code.

For completed requirements, preserve decisions that would otherwise need rediscovery. The entire diff and conversation belong in their original systems, not in the knowledge note. Small changes can update a topic without producing another requirement summary.
