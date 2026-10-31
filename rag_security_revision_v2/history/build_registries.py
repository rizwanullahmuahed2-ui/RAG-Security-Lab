"""Build read-only evidence and historical-reproduction registries.

Only writes this revision's history/ and the two explicitly assigned baseline
registries. It never edits historical data, scripts, scores or manuscripts.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
HISTORY = ROOT / 'history'
BASELINE = ROOT / 'baseline'
REPO = WORKSPACE / 'research_phase/repo_snapshot'
STUDY_B = WORKSPACE / 'revision/experiment'
COMMIT = '6f76858df91277e4b962ee94b4286a25cfe08d4d'
REPOSITORY = 'rizwanullahmuahed2-ui/RAG-Security-Lab'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def evidence(path, meaning):
    path = Path(path)
    assert path.is_file(), path
    return {'path': str(path), 'sha256': sha(path), 'meaning': meaning}


def refreshed(name):
    wrapped = read(HISTORY / f'refresh_{name}.json')
    response = wrapped['response']
    assert not response.get('isError'), name
    structured = response.get('structuredContent', {})
    payload = structured.get('content', structured)
    if isinstance(payload, str):
        payload = json.loads(payload)
    return wrapped, payload


def main():
    now = datetime.now(timezone.utc).isoformat()
    old = read(BASELINE / 'prior_files_sha256.json')['files']
    differences = []
    for relative, expected in old.items():
        path = WORKSPACE / relative
        if not path.is_file() or sha(path) != expected:
            differences.append(relative)
    assert not differences, differences

    branches_meta, branches = refreshed('branches')
    commits_meta, commits = refreshed('commits')
    releases_meta, releases = refreshed('releases')
    tags_meta, tags = refreshed('tag_matching_refs')
    runs_meta, runs = refreshed('workflow_runs')
    assert len(commits) == 3, 'History changed: extend the bounded search before concluding.'
    assert commits[0]['sha'] == COMMIT
    assert [p['sha'] for p in commits[0]['parents']] == [commits[1]['sha']]
    assert [p['sha'] for p in commits[1]['parents']] == [commits[2]['sha']]
    assert commits[2]['parents'] == []

    tree_records = []
    possible_archive_paths = []
    special_path_records = []
    tree_files = ['tree_main.json', 'tree_oct21.json', 'tree_initial.json']
    for name, commit in zip(tree_files, commits):
        raw = read(HISTORY / name)
        tree = raw['payload']
        assert not raw['is_error']
        assert not tree.get('truncated')
        assert tree['sha'] == commit['commit']['tree']['sha']
        blobs = [x for x in tree['tree'] if x['type'] == 'blob']
        listed = []
        for entry in blobs:
            path = entry['path']
            if any(term in path.lower() for term in ['results/', 'archive', 'records', 'manifest', '20260921', '21840', '3016']):
                listed.append({'path': path, 'git_blob_sha1': entry['sha'], 'bytes': entry.get('size')})
            if path.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz', '.7z')):
                possible_archive_paths.append({'commit': commit['sha'], **entry})
            if '20260921T061151Z_d1966106' in path or path.startswith('results/runs/') or path.startswith('results/question-comparisons/'):
                special_path_records.append({'commit': commit['sha'], **entry})
        tree_records.append({
            'commit': commit['sha'], 'tree_sha': tree['sha'], 'tree_truncated': False,
            'blob_count': len(blobs), 'local_response': name,
            'response_sha256': sha(HISTORY / name), 'evidence_candidate_paths': listed,
        })
    assert not possible_archive_paths, 'Inspect archive candidates rather than declaring them absent.'
    assert not special_path_records, 'Inspect historical run paths before deciding H0.'

    run_artifacts = []
    for run in runs['workflow_runs']:
        filename = f'refresh_workflow_artifacts_{run["id"]}.json'
        raw = read(HISTORY / filename)
        response = raw['response']
        assert not response.get('isError')
        artifacts = response['structuredContent']['artifacts']
        run_artifacts.append({
            'run_id': run['id'], 'name': run['name'], 'head_sha': run['head_sha'],
            'url': run['html_url'], 'returned_artifact_count': len(artifacts),
            'artifact_list_first_page_only': True, 'response_file': filename,
            'response_sha256': sha(HISTORY / filename),
        })

    search = {
        'created_at_utc': now, 'repository': REPOSITORY, 'pinned_commit': COMMIT,
        'refresh_completed_at_utc': max(branches_meta['retrieved_at_utc'], commits_meta['retrieved_at_utc'], runs_meta['retrieved_at_utc']),
        'visible_branches': [{'name': b['name'], 'sha': b['commit']['sha']} for b in branches],
        'commits': [{'sha': c['sha'], 'committed_at_utc': c['commit']['committer']['date'], 'message': c['commit']['message'], 'parents': [p['sha'] for p in c['parents']]} for c in commits],
        'main_chain_reaches_parentless_initial_commit': True,
        'recursive_trees': tree_records,
        'release_count_returned': len(releases), 'tag_matching_refs_count_returned': len(tags),
        'workflow_total_count_reported': runs['total_count'], 'workflow_runs_inspected': run_artifacts,
        'archive_extension_candidates_in_three_trees': possible_archive_paths,
        'principal_or_question_comparison_run_paths_in_three_trees': special_path_records,
        'unsupported_endpoints_preserved_as_failures': ['tags.json', 'workflow_artifacts.json'],
        'failed_endpoint_is_not_evidence_of_absence': True,
        'successful_alternatives': ['refresh_tag_matching_refs.json', 'refresh_workflow_artifacts_39705393558.json', 'refresh_workflow_artifacts_39650060943.json', 'refresh_workflow_artifacts_36682383040.json'],
        'limits': [
            'Only publicly visible branch/history and saved complete recursive trees were inspected; unreachable Git objects, deleted branches, private forks, local disks and backups outside this workspace were not searched.',
            'Three workflow artifact wrappers expose their first page. All returned an empty list; expired or deleted historical artifacts cannot be recovered or ruled out from these responses.',
            'No release or tag was returned at refresh time; this does not show that no such material ever existed.',
            'The committed 6.8 MB targeted diagnostic records are available remotely but were not downloaded or rescored by this history task; that protocol is separate from the principal and repetition experiments.',
        ],
    }
    dump(HISTORY / 'bounded_search_results.json', search)

    core_evidence = [
        evidence(REPO / 'research/README.md', 'Explicitly distinguishes the supplied historical manuscript from current code and says full historical archives are not bundled.'),
        evidence(REPO / 'README.md', 'Current workbench defaults and Git-ignored generated run directories.'),
        evidence(REPO / '.gitignore', 'results/runs/ excluded; explains publication practice, not independent proof of nonexistence.'),
        evidence(REPO / 'VALIDATION.md', 'Historical run ID and reported metrics; not its raw execution archive.'),
        evidence(WORKSPACE / 'research_phase/repo_audit/original_data_audit.json', 'Previously completed independent reconstruction and provenance checks of available canonical inputs.'),
        evidence(HISTORY / 'bounded_search_results.json', 'Fresh repository metadata and verified complete trees used in the bounded search.'),
    ]
    decision = {
        'created_at_utc': now, 'scope': 'P0/P3 implementation: evidence identity, bounded recovery search and explicit claim decision; no experimental replay',
        'primary_path': 'H0', 'principal_run_id': '20260921T061151Z_d1966106',
        'principal_archive_status': 'not_recovered_in_bounded_public_repository_search',
        'repetition_3016_archive_status': 'not_recovered_in_bounded_public_repository_search',
        'matching_principal_code_and_effective_config_status': 'not_recovered',
        'canonical_224_225_364_104_inputs_status': 'available_and_previously_reconstructed_independently',
        'separate_diagnostic_1092_status': 'remote_records_path_exists_summary_available_not_a_substitute_for_principal',
        'principal_fresh_rescoring_completed': False, 'principal_exact_replay_completed': False,
        'repetition_fresh_rescoring_completed': False, 'new_A_prime_executed': False,
        'new_A_prime_required_for_completion': False,
        'allowed_claims': [
            'The historical manuscript reports a 21,840-row extractive experiment and a separate 3,016-row repetition/accepted-label experiment.',
            'The canonical source tables and current workbench are publicly available at the specified commit, with independent input reconstruction documented in the prior audit.',
            'The exact completed principal/repetition archives were not recovered from the bounded accessible repository search, so their historical numerical outcomes are not independently re-established here.',
            'An explicitly new A-prime reimplementation may be performed if scientifically needed; it must name its code, input, config and deviations and cannot substitute for the missing historical archive.',
        ],
        'disallowed_claims': [
            'All historical results were freshly reproduced or independently certified.',
            'Current workbench source is the original principal runtime because counts and backend families resemble the paper.',
            'The 1,092-row diagnostic reproduces the 21,840-row principal or the 3,016-row repetition experiment.',
            'No original archive exists anywhere, was destroyed, or can never be recovered.',
            'A hash mismatch caused solely by LF/CRLF differences proves source-data tampering.',
        ],
        'branch_if_original_archive_later_supplied': ['verify original file hashes and run identity', 'link exact source/config/input/output', 'rescore saved outputs as H2', 'execute exact historical version only if possible as H3, documenting environmental differences'],
        'branch_if_new_A_prime_scientifically_needed': {'label': 'A-prime new reimplementation', 'historical_comparison_grid': {'n_questions': 364, 'budgets': [0,10,30,60,104], 'defenses': ['none','rerank','filter','filter_rerank'], 'attack_selection_seeds': [17,42,91], 'rows_if_all_executed': 21840}, 'requirement': 'Freeze before executing; identical row count does not imply an identical experiment.'},
        'repetition_gap': 'If original repetitions are not recovered and the separately designed fixed-target Study C dose module is not executed, the repetition analysis remains an explicit unresolved gap; reducing claims does not complete an unperformed experiment.',
        'evidence': core_evidence,
        'baseline_integrity': {'files_checked': len(old), 'changed_files': differences},
        'human_review': {'completed_here': 0, 'owner_latest_requirement': 'Keep genuine human semantic validation as pending work; do not present AI review or blank forms as a substitute.'},
    }
    dump(HISTORY / 'reproducibility_decision.json', decision)

    b_config = read(STUDY_B / 'config.json')
    b_completion = read(STUDY_B / 'completion.json')
    audit = read(WORKSPACE / 'research_phase/artifact_audit/audit_report.json')
    original_figures = read(WORKSPACE / 'revision/figures/original_figures_manifest.json')
    figures = []
    for item in original_figures['figures']:
        path = WORKSPACE / 'revision/figures' / item['file']
        assert sha(path) == item['image_sha256']
        figures.append({
            'file': str(path), 'sha256': sha(path), 'study': 'A_historical',
            'role': 'historical pipeline' if 'pipeline' in item['file'] else 'historical reported result',
            'original_pdf_page': item['original_page'],
            'preservation_requirement': 'Keep original bytes; if historical outcome cannot be re-established, retain versioned historical caption or appendix status. New results require a separate figure.',
        })
    path = WORKSPACE / 'revision/figures/generative_outcomes.png'
    figures.append({'file': str(path), 'sha256': sha(path), 'study': 'B_archived', 'role': 'archived numerical-containment outcomes', 'preservation_requirement': 'Keep as archived B numerical figure; corrected/semantic/reanalysis or C results must be separate and cannot silently replace the original.'})
    dump(HISTORY / 'figure_preservation_registry.json', {'created_at_utc': now, 'mandatory_figures': figures, 'mandatory_figure_count': 4, 'original_source_pdf_sha256': original_figures['source_pdf_sha256'], 'existing_figures_verified_unchanged': True, 'new_manuscript_embedding_not_yet_verified_by_this_task': True})

    studies = {
        'created_at_utc': now, 'status_time_scope': 'Entries describe evidence at registry creation; Study C and human-review entries must be updated from actual outputs after execution/review.',
        'repository': {'name': REPOSITORY, 'commit': COMMIT, 'paper_sha256': read(REPO / 'research/manifest.json')['sha256']},
        'studies': [
            {'id':'A_historical', 'kind':'reported extractive principal experiment', 'data':{'documents':224,'chunks':225,'questions':364,'targets':104}, 'grid':{'budgets':[0,10,30,60,104],'seeds':[17,42,91],'defenses':4,'correlated_rows_reported':21840}, 'active_components_reported':{'embedding':'hashing 1024d','retrieval':'exact cosine candidates','reranking':'query/candidate TF-IDF','answerer':'deterministic sentence extraction','candidate_k':30,'context_k':5}, 'evidence_level':'canonical inputs reconstructed; exact historical output/code/config archive not recovered', 'inference_limit':'No real generative LLM inference can be inferred from extractive historical results.', 'evidence_paths':[str(REPO/'research/README.md'),str(REPO/'VALIDATION.md'),str(HISTORY/'reproducibility_decision.json')]},
            {'id':'A_repetition_historical', 'kind':'separately reported target-specific repetition and accepted-label controls', 'correlated_rows_reported':3016, 'target_questions':104, 'corpus_scope':'separate corpus per target; not shared-corpus principal/B/C', 'archive_status':'not recovered', 'fresh_rescoring_completed':False, 'evidence_paths':[str(WORKSPACE/'revision/source_original_article.txt'),str(HISTORY/'reproducibility_decision.json')]},
            {'id':'A_diagnostic_committed', 'kind':'separate September 30 targeted-mode diagnostic', 'correlated_rows_reported':1092, 'n_questions':364, 'conditions':'clean, ten synthetic own-assertion copies, filtered', 'summary_available':True, 'full_records_remote_path':'results/targeted-mode-validation/records.json', 'full_records_git_blob_sha1':'29bd04ae120dcb5ba5057c779de6e7d3e2d14947', 'full_records_bytes':6822461, 'fresh_response_rescoring_completed_by_this_task':False, 'evidence_level':'summary and synthetic pool verified in prior audit; do not substitute for original principal run'},
            {'id':'repository_current_workbench', 'kind':'versioned software, not a frozen principal study', 'default_budgets':[0,10,20,50,104], 'active_components_at_default_config':{'embedding':'hashing-lexical-v2:1024d','retrieval':'eligible pool sentence lexical coverage/proximity, vector similarity tie-breaker','reranker':'lexical_overlap_tfidf','answerer':'extractive-evidence-v2','store':'exact'}, 'configured_but_inactive_defaults':['sentence-transformers/all-MiniLM-L6-v2','cross-encoder/ms-marco-MiniLM-L-6-v2','Anthropic generative backend'], 'backend_fallback_allowed_at_default':False, 'historical_identity':'not byte-identical to principal runtime; six files differ from separate diagnostic source manifest', 'evidence_paths':[str(REPO/'config.yaml'),str(REPO/'src/retrieval/retriever.py'),str(REPO/'src/generation/llm_interface.py')]},
            {'id':'B_archived', 'kind':'executed external real-LLM exploratory study', 'questions':64,'donors':64,'clean_paragraphs':640,'conditions':b_config['conditions'],'defenses':b_config['defenses'],'condition_rows':1280,'unique_generation_payloads_and_responses':376,'reused_condition_rows':904,'generation_rounds_per_unique_payload':1,'generator':b_config['generator'],'embedding':b_config['embedding_model'],'embedding_dimensions':1536,'retrieval':'frozen normalized API vectors, exact cosine, stable corpus-order ties','reranker':b_config['reranker'],'gate':b_config['filter'],'evidence_level':'saved payload/context/response hashes and all 1280 numerical outcomes independently reconstructed; semantic/human validation still pending','api_model_fallbacks':b_completion['model_fallbacks'],'completed_at_utc':b_completion['completed_at_utc'],'human_judgments_completed':0,'interpretation_limit':'numerical containment is not verified factual correctness or semantic adoption; the observed subset is now development/retrospective material for follow-up design','evidence_paths':[str(STUDY_B/'freeze.json'),str(STUDY_B/'generation_freeze.json'),str(STUDY_B/'completion.json'),str(WORKSPACE/'research_phase/artifact_audit/audit_report.json')]},
            {'id':'C_followup', 'kind':'prospective follow-up being implemented', 'execution_status_at_registry_creation':'in preparation; no completed result asserted by this registry', 'target_questions_planned':64,'donors_planned':64,'planned_generator':'gpt-4.1-mini-2025-04-14','planned_rounds':3,'planned_modules':['shared-corpus core','controlled exposure','fixed-target doses if prospectively included','retrieval-only legitimate-support rejection sensitivity'], 'freeze_requirement':'two stages: design/embedding requests first; vectors/contexts/generation requests second before generation', 'human_review_requirement':'retained as pending genuine human work per owner clarification; no AI/human substitution', 'update_rule':'After actual execution, replace planned sizes/model/requests/status with observed manifests and preserve this earlier registry as provenance.'},
        ],
        'trust_roles': {
            'label_assigner_supported_by_evidence':'dataset constructor supplies label fields',
            'real_authorized_person_or_institution_for_document_approval':None,
            'printed_affiliation_is_not_document_approval_evidence':True,
            'implemented_authorization_authentication_signature_protected_audit_workflow':False,
            'base_attack':'poison text is supplied with rejected labels',
            'accepted_label_intervention':'direct test-fixture change of verified/trust fields on identical target text, not demonstrated intrusion into an approval process',
            'approved_claim':'effect conditional on supplied eligibility labels',
            'unsupported_claim':'deployed institutional source authentication or resistance to unauthorized approval modification',
        },
        'architecture_decision_provenance': {
            'current_documented_rationale':'dependency-light deterministic offline workbench permits auditable local evaluation; documented current design rationale, not reconstructed original intent',
            'historical_reported_rationale':'VALIDATION.md says approximate Chroma variability motivated exact search; original trial archive and contemporaneous decision log were not recovered',
            'original_proposal_or_decision_log_status':'not recovered from inspected repository material',
            'rule':'Do not infer that a configured model name was active or invent a historical reason for omitted components.'},
        'figures_registry':str(HISTORY/'figure_preservation_registry.json'),
    }
    dump(BASELINE / 'study_registry.json', studies)

    defs = []
    def claim(cid, study, text, status, action, paths, limitation):
        defs.append({'id':cid,'study':study,'claim':text,'evidence_status':status,'manuscript_action':action,'limitation':limitation,'evidence':[evidence(path, meaning) for path,meaning in paths]})
    A = [(REPO/'research/README.md','Historical/current boundary'),(HISTORY/'reproducibility_decision.json','Bounded archive recovery decision')]
    B = [(STUDY_B/'completion.json','Executed model and response count'),(WORKSPACE/'research_phase/artifact_audit/audit_report.json','Independent archived numerical audit')]
    claim('A-inputs','A_historical','224 documents, 225 chunks, 364 questions and 104 attacks are publicly available and their construction is auditable.','verified_input_availability','Update old blanket-unavailability wording.',[(WORKSPACE/'research_phase/repo_audit/original_data_audit.json','Canonical reconstruction'),(REPO/'data/dataset_manifest.json','Input provenance hashes')],'Snapshot reconstruction does not independently authenticate all inherited facts or reproduce historical output.')
    claim('A-replay','A_historical','The original 21,840-row principal execution has been freshly reproduced.','unsupported_in_present_revision','Do not assert; retain only reported historical numbers with explicit missing-archive limit.',A,'Exact original response archive, matching source/config and run manifest were not recovered.')
    claim('A-endpoints','A_historical','At full budget, historical no-defense ASR was 73.1% and reranked ASR 72.1%.','historically_reported_not_freshly_reestablished','Historical context only; caption and table identify reported source.',[(REPO/'VALIDATION.md','Reported principal summary'),(WORKSPACE/'revision/source_original_article.txt','Historical manuscript')],'No independent response-level recalculation in current implementation.')
    claim('A-repetition','A_repetition_historical','The 3,016-row repetition/accepted-label study has response-level reproducibility evidence here.','not_recovered','Mark archive gap; do not pool with C doses or committed diagnostic.',A,'If neither original nor new repetition analysis is available, its expert-comment gap remains open.')
    claim('A-current-code','repository_current_workbench','Current public workbench is the original principal implementation.','contradicted_by_version_evidence','Distinguish versions and active ranking behavior.',[(REPO/'config.yaml','Current budgets'),(REPO/'src/retrieval/retriever.py','Current lexical ranking'),(WORKSPACE/'research_phase/repo_audit/diagnostic_source_hash_comparison.json','Version differences')],'Backend-family and row-count similarity cannot establish code identity.')
    claim('A-unit','A_historical','21,840 rows are independent experimental samples.','invalid_unit_claim','Use question/fact groups and distinguish attack-selection seeds.',[(WORKSPACE/'research_phase/repo_audit/original_data_audit.json','168 facts with two phrasings and related years')],'Three selection seeds are not repeated generative draws.')
    claim('A-clean-cost','A_historical','No observed clean cost proves safe rejection of legitimate documents.','unsupported_generalization','Report narrow benchmark observation and coverage limitation.',[(WORKSPACE/'research_phase/repo_audit/original_data_audit.json','Two rejected mineral chunks have no gold question')],'The rejected legitimate facts are not directly tested by the original question set.')
    claim('B-real-model','B_archived','Study B used real gpt-4.1-mini-2025-04-14 inference and neural API embeddings.','supported_by_saved_execution_evidence','Retain actual model and executed-scope statement.',B,'Archive consistency is not third-party provider-origin certification.')
    claim('B-counts','B_archived','1,280 condition rows represent 376 distinct generation requests and 904 reuses.','independently_reconstructed','Report both condition and unique-request counts.',B,'Cached condition reuse does not create independent generations.')
    claim('B-score','B_archived','34/64 targeted and 17/64 reranked outputs contain only the designated false number.','numeric_recomputed_semantic_status_pending','Keep archived numerical results; attach separate reference and evaluator reanalysis.',B,'Some designated false values/references require source adjudication; number presence is not semantic endorsement.')
    claim('B-semantic','B_archived','The numerical accuracy field establishes factual correctness.','unsupported_semantic_interpretation','Name lexical/numerical metric accurately and report separate evaluation axes.',B,'Negation, qualifications, wrong entities and UNKNOWN-plus-number cases require interpretation.')
    claim('B-controls','B_archived','Targeted versus unrelated results isolate generator robustness at equal exposure.','unsupported_control_interpretation','Call it end-to-end targeting; use separately fixed-context follow-up for equal exposure.',B,'Targeted any-insertion exposure is 64/64 versus 16/64 unrelated without defense.')
    claim('B-rerank','B_archived','Reducing success from 34 to 17 means 17 attacks were prevented with no new failures.','incorrect_transition_interpretation','Report 24 prevented, 11 numerical restorations and 7 newly successful cases.',[(WORKSPACE/'research_phase/artifact_audit/audit_report.json','Paired outcome audit'),(STUDY_B/'paired_defense_outcomes.csv','Archived transitions')],'Net endpoint difference conceals newly introduced failures and incomplete restoration.')
    claim('B-filter','B_archived','Filtering demonstrates operational authentication or fact checking.','not_implemented','Describe an ideal supplied-label gate and its exact predicate.',[(STUDY_B/'config.json','All clean labels accepted; base insertions rejected')],'The trusted-label authority, authentication, protected audit and authorization workflow are not implemented.')
    claim('B-label-change','B_archived','Accepted-label experiment demonstrates a real compromise of document approval.','not_demonstrated','Call it metadata-only intervention in attacker capability.',[(STUDY_B/'config.json','Text unchanged; accepted-label fields changed'),(STUDY_B/'insertions.json','Insertion text/IDs')],'Direct field mutation in a fixture is not an intrusion test.')
    claim('B-then-heldout','B_archived','The 64 questions remain untouched final test data for tuning the follow-up.','no_longer_applicable_after_inspection','Keep B retrospective and use new prospectively frozen follow-up cases.',[(STUDY_B/'freeze.json','Original pre-output freeze'),(WORKSPACE/'research_phase/Research_Stage_Report_FA.md','Subsequent inspection and diagnostics')],'Original held-out output timing does not restore freshness after observed outcomes guide changes.')
    claim('B-A-causal','A_historical/B_archived','Differences between A and B isolate the effect of replacing extraction by an LLM.','unsupported_causal_comparison','Report studies separately.',[(BASELINE/'study_registry.json','Dataset and retrieval changes')],'Material, retriever, attack grid and answerer all differ.')
    claim('B-guard','B_archived','A weak empty-cache pre-dispatch guard proves archived results were tampered with.','not_supported','Fix guard prospectively without accusing the valid archive.',[(WORKSPACE/'research_phase/artifact_audit/guard_check_result.json','Offline fake-transport demonstration'),(WORKSPACE/'research_phase/artifact_audit/audit_report.json','All archived hashes match')],'Preventive weakness and evidence of historical tampering are separate questions.')
    claim('Human-review','B_archived/C_followup','Independent human semantic review has been completed.','not_completed','Keep genuine review as pending and prepare reviewer materials; no invented human labels.',[(STUDY_B/'human_review_blinded.csv','Original empty human fields'),(WORKSPACE/'research_phase/artifact_audit/audit_report.json','Zero completed human judgments')],'Owner explicitly requested that this work not be dropped; AI source audit and deterministic metrics cannot complete it.')
    claim('Trust-authority','all','Printed affiliation identifies the actual authorized institutional approver of every source.','not_established','State only dataset-constructor label assignment unless real approval evidence is supplied.',[(REPO/'research/manifest.json','Affiliation as printed only'),(BASELINE/'study_registry.json','Trust-role boundary')],'No named official, approval record or authorization service is evidenced by these fields.')
    claim('Repository-public','all','No public repository exists for this project.','outdated','Cite pinned public repository while distinguishing local B/C artifacts from committed contents.',[(REPO/'research/README.md','Public repository and original historical statement'),(HISTORY/'refresh_branches.json','Current accessible main')],'Public code and canonical inputs do not imply all historical runs or the local new studies were published.')
    claim('Provenance-auth','all','Local hashes establish source authenticity and truth.','unsupported_generalization','Use hashes for archive identity/integrity only.',[(WORKSPACE/'research_phase/repository_snapshot_manifest.json','Selected file identity'),(STUDY_B/'generation_freeze.json','Pre-generation artifacts')],'A matching digest does not certify factual truth, provider origin or approval authority.')
    claim('Pretraining','B_archived/C_followup','Public benchmark selection proves independence from model pretraining.','not_established','Disclose public source and restricted overlap checks.',[(STUDY_B/'source_dataset_metadata.json','Pinned public HotpotQA source'),(WORKSPACE/'research_phase/repo_audit/cross_study_overlap.json','Bounded input comparison')],'No pretraining-membership test or source-family independence proof was performed.')
    claim('Figures','A_historical/B_archived','All four existing figures are preserved unchanged as source assets.','verified_bytes_at_registry_creation','Preserve originals and captions/version labels in final manuscript; separately add changed-result figures.',[(HISTORY/'figure_preservation_registry.json','Four asset hashes checked')],'Final PDF/DOCX embedding and caption accuracy must still be checked during release.')
    claim('C-executed','C_followup','The new follow-up experiment has produced final results.','not_asserted_at_registry_creation','Fill only from actual completed frozen-run manifests after execution.',[(WORKSPACE/'implementation_plan/Experiment_Blueprint.json','Proposed design, not results')],'Planning or dataset preparation is not completed real inference.')
    registry = {
        'created_at_utc': now, 'purpose':'Claim-to-evidence ledger implemented before follow-up results; source files are immutable and each evidence path is hashed.',
        'evidence_vocabulary':{'verified_input_availability':'availability/construction checked, not factual certification','independently_reconstructed':'independent calculation from archived local inputs/outputs, not independent human adjudication','historically_reported_not_freshly_reestablished':'retain only attributed historical context','not_completed':'explicit pending work; no completion claim'},
        'claims':defs, 'claim_count':len(defs),
        'mandatory_preservation':{'baseline_files_checked':len(old),'changed_files':differences,'four_figures':str(HISTORY/'figure_preservation_registry.json')},
        'required_live_updates_after_root_execution':['C-executed actual run status and final counts','Human-review actual human records/status','Figures final PDF/DOCX embedding/caption check','new reference audit and evaluator outputs appended as evidence rather than overwriting archived B scores'],
    }
    dump(BASELINE/'claims_registry.json',registry)

    report = '''# تصمیم مستند دربارهٔ بازتولید تاریخی و حدود ادعاها

## نتیجهٔ بررسی

ورودی‌های اصلی تحقیق و کد فعلی در مخزن عمومی موجود است. با این حال، در جست‌وجوی محدود و ثبت‌شدهٔ این مرحله، آرشیو کامل اجرای اصلی ۲۱٬۸۴۰ردیفی، آرشیو مکمل ۳٬۰۱۶ردیفی و کد و تنظیمات منطبق با اجرای اصلی بازیابی نشد. بنابراین، مسیر فعلی **H0: ثبت عدم بازیابی و محدودکردن ادعا** است. این تصمیم، اثبات نبودن فایل‌ها در همهٔ محل‌ها یا ناممکن‌بودن بازیابی بعدی نیست.

## چه چیز واقعاً بررسی شد

معلومات مخزن در ۲۶ اکتوبر ۲۰۲۶ دوباره از GitHub خوانده شد. فقط شاخهٔ main و همان سه commit برگشت داده شد. زنجیرهٔ والدها تا commit اولیهٔ بدون والد کامل است. درخت بازگشتی هر سه نسخه موجود و بدون علامت truncation است؛ به‌ترتیب ۱۲۱، ۱۱۸ و ۱۰۴ فایل باینری یا متنی در آن‌ها ثبت شده است. مسیر اجرای `20260921T061151Z_d1966106` و آرشیو پوشهٔ runs در این درخت‌ها وجود ندارد.

هیچ release یا tag در پاسخ‌های موفق فعلی برگشت داده نشد. سه اجرای workflow قابل مشاهده بود؛ فهرست artifact هر سه خالی برگشت. این فهرست‌ها از wrapper صفحهٔ اول خوانده شده‌اند. فایل منقضی یا حذف‌شده از این پاسخ‌ها قابل بازیابی یا رد قطعی نیست. endpointهای ناموفق قبلی نگهداری شده‌اند و دلیل نبودن داده محسوب نشده‌اند؛ برای tag از matching-refs و برای artifact از ابزار اختصاصی هر workflow استفاده شد.

در مخزن، مسیر رکوردهای آزمایش تشخیصی ۱٬۰۹۲ردیفی موجود است. آن آزمایش با ۳۶۴ پرسش و ده نسخهٔ ادعای مصنوعی مخصوص هر هدف کار کرده است. شمار آن، پروتکل آن و نام backend با آزمایش اصلی فرق دارد. وجود این رکوردها، بازیابی اجرای اصلی یا مکمل تکرار محسوب نمی‌شود. فایل ۶٫۸مگابایتی آن در این کار دانلود یا بازنمره‌دهی نشد.

## نتیجه برای مقاله

عبارت کلی «دیتا و کد اصلی در دسترس نیست» باید اصلاح شود، زیرا چهار جدول canonical و کد فعلی واقعاً موجود و قابل بررسی‌اند. در مقابل، ادعای «تمام نتایج تاریخی بازتولید شد» پشتیبانی ندارد. ارقام و نمودارهای تاریخی باید با نام نسخه و عبارت گزارش‌شدهٔ قبلی محفوظ بمانند. شواهد مطالعهٔ مولد B و اجرای تازهٔ C، جای آرشیو A را نمی‌گیرند.

کد فعلی، نسخهٔ منجمد اجرای اصلی نیست. بودجه‌های پیش‌فرض آن صفر، ۱۰، ۲۰، ۵۰ و ۱۰۴ است؛ بودجه‌های گزارش اصلی صفر، ۱۰، ۳۰، ۶۰ و ۱۰۴ بود. در backend فعلی، پوشش و نزدیکی واژگانی جمله در رتبه‌بندی دخالت دارد و شباهت برداری نقش شکست تساوی دارد. گزارش اصلی، نامزدهای exact cosine و استخراج قبلی را توصیف کرده است. یکسان‌بودن خانوادهٔ روش یا تعداد ردیف‌ها، این اختلاف نسخه را از میان نمی‌برد.

اگر مقایسهٔ تازه روی دیتای قدیمی برای سؤال تحقیق ضروری باشد، A′ با نام مستقل، کد، ورودی، تنظیمات و اختلاف‌های مستند اجرا می‌شود. اجرای آن شرط خودکار پایان کل مقاله نیست و بازتولید دقیق A معرفی نخواهد شد. اگر آرشیو اصلی بعداً فراهم شود، نخست هویت فایل‌ها، پیوند نسخه‌ها و رکوردهای اصلی بررسی و سپس بازنمره‌دهی و بازاجرا جدا گزارش می‌شود.

برای تحلیل تکرار، اگر هم آرشیو قبلی بازیابی نشود و هم ماژول تازهٔ ثابت‌هدف اجرا نشود، شکاف مربوط صریح باز می‌ماند. محدودکردن ادعا، اجرای آزمایشی که انجام نشده را تکمیل نمی‌کند.

## حدود اعتماد و نگارش

صفت اعتماد در شواهد فعلی توسط سازندهٔ دیتای آزمایش تعیین شده است. شخص یا نهاد واقعی صاحب صلاحیت تأیید سند، روند احراز هویت، امضای سند و ثبت حفاظت‌شدهٔ تغییر برچسب در این مواد اثبات نشده است. وابستگی چاپ‌شدهٔ نویسندگان، جای سند صلاحیت تأیید هر منبع را نمی‌گیرد. تغییر مستقیم دو فیلد برچسب در آزمایش، آزمون نفوذ به روند تأیید نیست.

بررسی انسانی معنایی نیز کنار گذاشته نشده است؛ تا ورود داوری واقعی، وضعیت آن «در انتظار» می‌ماند. بررسی دستیار، تطبیق عدد و فرم خالی، داوری انسانی نامیده نمی‌شود.

## مواد تحویل این کار

`bounded_search_results.json` دامنه و نتایج جست‌وجو را ثبت می‌کند. `reproducibility_decision.json` مسیر H0، ادعاهای مجاز و نامجاز و شرط تغییر مسیر را نگه می‌دارد. دو دفتر `baseline/study_registry.json` و `baseline/claims_registry.json`، مطالعه‌ها و هر ادعا را به فایل شاهد و هش آن وصل می‌کنند. `figure_preservation_registry.json` هش چهار شکل موجود را ثبت کرده است؛ سه شکل تاریخی و نمودار B محفوظ‌اند و نتیجهٔ تازه نباید خاموش جای آن‌ها بنشیند.

همهٔ ۲۴۴ فایل baseline قبلی در این کار با هش ثبت‌شده تطبیق داشتند و تغییر نکردند. این کار هیچ مدل یا آزمایش تازه اجرا نکرده، داوری انسانی نساخته و آرشیو تاریخی را تغییر نداده است.
'''
    (HISTORY/'reproducibility_decision.md').write_text(report)
    dump(HISTORY/'registry_build_checks.json',{
        'created_at_utc':now, 'baseline_files_checked':len(old),'baseline_files_changed':differences,
        'fresh_git_metadata_requests':8, 'trees_inspected':len(tree_records),'tree_blob_counts':[r['blob_count'] for r in tree_records],
        'visible_commits':len(commits),'visible_workflow_runs':len(run_artifacts),
        'claims_registered':len(defs),'studies_registered':len(studies['studies']),
        'mandatory_figures_hash_checked':len(figures),'new_llm_calls':0,'human_judgments':0,
        'original_principal_replay_executed':False,'new_A_prime_executed':False,
    })
    print(json.dumps({'claims':len(defs),'studies':len(studies['studies']),'figures':len(figures),'baseline_checked':len(old),'archive_decision':'H0'},ensure_ascii=False))


if __name__ == '__main__':
    main()
