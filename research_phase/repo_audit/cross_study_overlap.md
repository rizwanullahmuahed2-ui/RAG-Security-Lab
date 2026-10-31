# Bounded cross-study overlap check

This post hoc read-only check compares the recovered current canonical Afghanistan inputs with the saved HotpotQA Study B material. It does not change either dataset and makes no network or model call.

## Scope

Compared 364 Study A question strings with 64 test and 64 donor questions; 224 original document titles with 1280 selected context titles; and 449 document/chunk text fields with 640 indexed Study B paragraphs, both with and without the added title prefix. Annotated support sentences from both test and donor records were also compared.

| Normalization | Questions | Titles | Full prefixed paragraphs | Paragraph bodies | Whole clean text vs support sentence |
|:--|--:|--:|--:|--:|--:|
| NFKC_casefold_whitespace | 0 | 0 | 0 | 0 | 0 |
| NFKC_casefold_alphanumeric_tokens | 0 | 0 | 0 | 0 | 0 |

## Literal phrase and keyword checks

Shared eight-token phrase records: 0; shared twelve-token phrase records: 0. These are literal phrase checks, not semantic judgments.

- Afghanistan: questions=0, selected_context_titles=0, paragraph_bodies=0
- Kabul: questions=0, selected_context_titles=0, paragraph_bodies=0
- Bamiyan: questions=0, selected_context_titles=0, paragraph_bodies=0
- Kandahar: questions=0, selected_context_titles=0, paragraph_bodies=0
- Herat: questions=0, selected_context_titles=0, paragraph_bodies=0
- Hindu Kush: questions=0, selected_context_titles=0, paragraph_bodies=0
- World Bank: questions=0, selected_context_titles=0, paragraph_bodies=0

## What this supports

These checks provide a concrete exact-overlap result now that original canonical inputs are accessible. Any claim must name the compared Git revision, Study B subset and normalization rules.

## What it does not support

- Zero exact matches would rule out only duplicate strings under the specified normalizations, not paraphrases, same entities, same facts, or shared source families.
- Donor full context paragraphs are not retained in the local Study B donor file; donor questions, context titles and annotated support sentences were inspected, not their full paragraph bodies.
- Only committed current canonical Study A inputs at this Git revision were compared; exact historical principal-run input identity is not established without its missing manifest/archive.
- Both studies draw on publicly available material. These checks do not establish independence from model pretraining, and no model-contamination test was performed.
- Shared short phrases or domain keywords, if present, are literal overlap findings, not proof of identical underlying facts.
