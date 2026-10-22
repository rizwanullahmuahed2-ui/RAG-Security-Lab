# RAG security manuscript

[Read the paper (PDF)](RAG_Security_Research.pdf) · [BibTeX citation](CITATION.bib) · [File manifest](manifest.json)

**Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning**

*An exploratory offline study of retrieval and extractive answer selection*

**Authors, in printed order:** Rizwanullah Muahed; Ramiz Mumtaz; Ebrahim Adham; Masihullah Yaqubi; Rohid Sharifi.

**Affiliation:** Department of Research and Development (R&D), Ministry of Communications and Information Technology.

**Status:** Unpublished manuscript supplied by the project owner. Approval was previously reported by the owner; the manuscript itself does not claim formal institutional approval or journal acceptance. No publication venue, date or DOI is assigned here.

The original 18-page PDF is preserved without edits. The [manifest](manifest.json) records its title, authors, page count, original filename and SHA-256 fingerprint. PDF creation timestamps are not treated as publication dates.

## What the paper describes

The principal experiment uses 224 documents, 225 chunks, 364 questions and 104 targets, with 21,840 correlated question-condition observations. Its actual backends are 1,024-dimensional hashing, exact cosine retrieval, TF-IDF reranking and deterministic sentence extraction. The paper explicitly distinguishes these results from generative LLM behavior.

The study separates gold-evidence recovery, malicious exposure, targeted answer corruption and correct-answer restoration. It also records the limits of trust-label filtering when accepted metadata can be forged.

## Relationship to the current code

The repository's default offline workbench uses the same broad backend family, but its current code is not a frozen copy of the historical experiment. The manuscript reports an archived principal run and later version-sensitive diagnostics. The full archived run and the separate development records named in Appendix D are not bundled by this PDF upload.

Appendix D reports neural retrieval controls and a 24-response GPT development pilot, with separate protocols and limits. The current repository documents an optional Anthropic integration; the pilot in the paper is not evidence that an OpenAI experiment is implemented or reproduced here.

The paper's historical statement that no public repository is claimed describes the supplied document. This repository now provides a public software implementation and the manuscript; that does not retroactively publish its missing experiment archives or independently validate its numbers.

See the [implementation](../README.md), [dataset card](../data/DATASET_CARD.md), [historical validation](../VALIDATION.md) and [current verification notes](../REVIEW_NOTES.md) for available evidence and reproduction commands.
