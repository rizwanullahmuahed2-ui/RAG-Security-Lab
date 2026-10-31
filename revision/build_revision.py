"""Build the revised manuscript and figures from the executed evidence."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
EXP = ROOT/"experiment"


def one_decimal(value):
    return str(Decimal(str(value)).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP))


def main():
    a = json.loads((EXP/"analysis.json").read_text())
    summary = {(r['condition'],r['defense']):r for r in a['summary']}
    rows = list(csv.DictReader((EXP/'scored_results.csv').open()))
    diagnostic = []
    for condition in ['clean','targeted','unrelated','benign','accepted_label']:
        for defense in ['none','rerank','filter','filter_rerank']:
            group = [r for r in rows if r['condition']==condition and r['defense']==defense]
            diagnostic.append({'condition':condition,'defense':defense,
                               'gold_only_with_unknown_language':sum(r['numeric_gold_only']=='1' and bool(re.search(r'\bunknown\b',r['answer'],re.I)) for r in group)})
    (EXP/'posthoc_output_diagnostics.json').write_text(json.dumps({'status':'post hoc output-format diagnostic; primary scores unchanged','groups':diagnostic},indent=2)+'\n')
    nice_c={'clean':'Clean','targeted':'Targeted','unrelated':'Unrelated','benign':'Benign','accepted_label':'Accepted label'}
    nice_d={'none':'None','rerank':'Rerank','filter':'Filter','filter_rerank':'Filter + rerank'}
    main_table=['| Corpus | Defense | Support | Exposure | Gold | False | EM |',
                '|:----------------|:----------------|------------:|------------:|----------:|----------:|----------:|']
    for s in a['summary']:
        metrics=['all_support_mean','assigned_insert_exposed_mean','numeric_gold_only_mean','numeric_false_only_mean','strict_em_mean']
        main_table.append('| '+nice_c[s['condition']]+' | '+nice_d[s['defense']]+' | '+' | '.join(one_decimal(100*s[m]) for m in metrics)+' |')
    contrasts=['**Table 5. Primary paired contrasts under no defense (percentage points). Intervals are exploratory 95% question bootstrap intervals conditional on the frozen corpus and responses.**','',
               '| Contrast | Outcome | Difference (pp) | Interval (pp) |','|:--|:--|--:|:--|']
    for s in a['contrasts'][:4]:
        outcome='False-only output' if s['metric']=='numeric_false_only' else 'Gold-only accuracy'
        contrasts.append(f"| Targeted − {nice_c[s['condition_b']].lower()} | {outcome} | {s['difference_pp']:+.1f} | {s['ci95_low_pp']:+.1f} to {s['ci95_high_pp']:+.1f} |")
    paired=['| Corpus | Defense | Prevented | Gold value restored | New successes |','|:--|:--|--:|--:|--:|']
    for s in a['paired_defense_outcomes']:
        paired.append(f"| {nice_c[s['condition']]} | {nice_d[s['defense']]} | {s['prevented']}/{s['initial_successes']} | {s['gold_value_restored']}/{s['initial_successes']} | {s['new_successes']} |")
    texts={
      'UNIQUE_CALLS':str(a['unique_generation_calls']),
      'REUSED_ROWS':str(a['cache_reused_rows']),
      'ABSTRACT_RESULTS':'Without defense, targeted poison produces the designated false value for 34/64 questions (53.1%), versus 0/64 under unrelated poison, while gold-only numerical accuracy is 37.5% versus 62.5%. Reranking reduces false-only outputs to 17/64. Filtering rejects all base insertions, but accepting the identical poisoned passages restores 34/64 false-only outputs under filtering alone.',
      'EXECUTION_STATUS':'All 376 unique generation requests returned the specified snapshot and a normal stop reason; no API error, output truncation, or model fallback occurred. Integrity and completeness checks passed.',
      'MAIN_TABLE':'\n'.join(main_table),
      'PRIMARY_CONTRASTS':'\n'.join(contrasts),
      'PAIRED_TABLE':'\n'.join(paired),
      'RQ1_RESULTS':'Without defense, targeted poison produces the designated false value for 34/64 questions (53.1%). The unrelated and benign controls each produce 0/64 designated false values, even though unrelated insertions contain the same false integers. Gold-only numerical accuracy is 24/64 (37.5%) under targeted poison, compared with 40/64 (62.5%) under unrelated poison, 41/64 (64.1%) on the clean corpus, and 64/64 (100.0%) under truthful question-shaped insertion. The targeted-minus-unrelated false-output difference is +53.1 percentage points (exploratory interval +40.6 to +65.6); its accuracy difference is −25.0 points (−37.5 to −12.5). Compared with benign insertion, the accuracy difference is −62.5 points (−73.4 to −50.0). These paired contrasts answer RQ1 for the implemented attack and numerical subset; they do not establish an optimized attack success probability.',
      'RQ2_RESULTS':'The clean undefended collection retains all annotated supporting passages for 36/64 questions (56.3%). Targeted poisoning reduces this to 30/64 (46.9%), while its assigned attack is retrieved for all 64 targets. Eight questions retain all annotated supporting passages and nevertheless produce the designated false value. With reranking, all-support recall is 24/64 (37.5%) and own-poison exposure is 36/64 (56.3%); four questions still retain every annotated support and produce the designated false value. Unlike Study A, reranking in this external study does not recover more gold evidence: it reduces both supporting-passage coverage and malicious exposure. Its lower false-output rate therefore cannot be described as evidence recovery alone. Of the 41 questions with a gold-only clean output, 17 (41.5%) produce the false value after undefended targeted poisoning. The remaining 17 targeted false outputs occur on questions already lacking a gold-only clean output, so 34 successes should not be interpreted as 34 newly lost correct answers.',
      'RQ3_RESULTS':'In the targeted condition, reranking reduces exposure-confirmed false outputs from 34/64 to 17/64 (26.6%). Paired transitions show 24/34 baseline successes prevented (70.6%), 11/34 reference values restored (32.4%), and seven newly successful attacks. The net decrease of 17 successes therefore conceals both prevention and new failures. Rejected-label filtering removes all attack exposure and prevents all 34 baseline successes, restoring 17/34 reference values; filtering followed by reranking restores 19/34. Under accepted-label compromise, filtering alone retains 34/64 false-only outputs, and filtering plus reranking retains 17/64. Its loss of protection follows solely from the changed supplied labels and resulting passage eligibility.',
      'RQ4_RESULTS':'Clean gold-only numerical accuracy is 41/64 (64.1%) without defense and 39/64 (60.9%) with reranking, a net cost of 3.1 percentage points. Filtering alone preserves 41/64, and filtering plus reranking preserves 39/64. Strict EM, however, changes from 22/64 (34.4%) without defense to 25/64 (39.1%) with reranking, an improvement of 4.7 points. Thus the clean-cost conclusion depends on the declared metric, rather than representing a uniform deterioration in every measure. Gold-only value matching can credit explanatory text that EM rejects. A post hoc format diagnostic also flags clean responses containing both the reference value and explicit UNKNOWN language; these flags do not change the frozen primary rule. No mixed gold-and-designated-false output occurs, and every API response terminates normally.',
      'DISCUSSION_SPECIFICITY':'On the fixed external subset, a question-addressed false assertion produces substantially more designated false values than a matched unrelated false assertion. The unrelated corpus changes accuracy only from 41/64 to 40/64 under no defense, whereas the targeted corpus reduces it to 24/64. Truthful question-addressed insertions produce 64/64 numerical matches. Together these observations support target alignment and asserted value as consequential properties under this protocol, rather than generic corpus expansion alone. They do not prove that unrelated poisoning is harmless in other domains, at other doses, or with different retrieval methods.',
      'CONCLUSION_RESULTS':'Targeted poison produces 34/64 designated false values without defense, compared with zero under matched unrelated poison; reranking reduces this to 17/64 while producing new failures and incomplete restoration. The gate eliminates rejected insertions by construction, and identical accepted-label poison removes that protection.',
      'PROVENANCE_SUMMARY':f"The run used Python 3.12.14, NumPy 2.3.5, and scikit-learn 1.8.0. Generation usage across the {a['unique_generation_calls']} unique study requests was {a['usage']['prompt_tokens']:,} input tokens and {a['usage']['completion_tokens']:,} output tokens; embedding usage was {a['embedding_usage_total_tokens']:,} tokens. Usage excludes the separate connectivity check. No invoice amount or operational latency comparison is claimed. The input-freeze SHA-256 is `ad8f1238e5c1624dca09d1c777f175e4633811e7d1d5301d3d6314f32b2208f7`. The generation-context and request hashes are recorded in `generation_freeze.json`; raw-response hashes and model IDs were checked before rescoring.",
    }
    original=(ROOT/'source_original_article.txt').read_text()
    refs=original.split('\nReferences\n',1)[1].split('Appendix A.',1)[0]
    refs=re.sub(r'\s*Research manuscript \| \d+\s*','\n',refs).replace('\f','')
    refs='\n\n'.join(' '.join(block.split()) for block in re.split(r'\n(?=\[\d+\])',refs.strip()))
    refs+='\n\n[22] OpenAI. GPT-4.1 mini model documentation and Chat Completions API. Snapshot used: gpt-4.1-mini-2025-04-14. https://developers.openai.com/api/docs/models/gpt-4.1-mini ; https://developers.openai.com/api/reference/resources/chat\n\n[23] OpenAI. text-embedding-3-small model documentation. 1,536-dimensional configuration used in this study. https://developers.openai.com/api/docs/models/text-embedding-3-small\n\n[24] HotpotQA authors. HotpotQA dataset and Hugging Face distribution, distractor validation split. Revision 1908d6afbbead072334abe2965f91bd2709910ab. CC BY-SA 4.0. https://hotpotqa.github.io/ ; https://huggingface.co/datasets/hotpotqa/hotpot_qa'
    texts['REFERENCES']=refs
    texts['REFERENCES']+='\n\n[25] Rizwanullah Muahed, Ramiz Mumtaz, Ebrahim Adham, Masihullah Yaqubi, and Rohid Sharifi. 2026. Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning: An exploratory offline study of retrieval and extractive answer selection. Unpublished historical research manuscript with development appendices. Archival source identified in the figure-provenance manifest.'
    texts['PROVENANCE_SUMMARY']=texts['PROVENANCE_SUMMARY'].replace('is `ad8f1238e5c1624dca09d1c777f175e4633811e7d1d5301d3d6314f32b2208f7`.','is:\n\n```\nad8f1238e5c1624dca09d1c777f175e4633811e7d1d5301d3d6314f32b2208f7\n```\n\n')
    template=(ROOT/'manuscript_template.md').read_text()
    for k,v in texts.items():template=template.replace('{{'+k+'}}',v)
    assert not re.search(r'\{\{[A-Z_]+\}\}',template)
    (ROOT/'Revised_Manuscript.md').write_text(template)
    figures=ROOT/'figures';figures.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
    fig,axes=plt.subplots(2,1,figsize=(8,6.6),sharex=True)
    conditions=['clean','targeted','unrelated','benign','accepted_label']
    defenses=['none','rerank','filter','filter_rerank']
    colors=['#173f5f','#ed8b24','#278779','#985aa1']
    x=np.arange(5);width=.19
    for ax,metric,title in zip(axes,['numeric_gold_only_mean','numeric_false_only_mean'],['Reference numerical value only','Designated false value only']):
        for j,(defense,color) in enumerate(zip(defenses,colors)):
            values=[100*summary[(c,defense)][metric] for c in conditions]
            ax.bar(x+(j-1.5)*width,values,width,label=nice_d[defense],color=color,zorder=3)
        ax.set_ylim(0,110);ax.set_yticks([0,25,50,75,100]);ax.set_ylabel('Questions (%)');ax.set_title(title,loc='left',fontweight='bold',pad=8)
        ax.grid(axis='y',alpha=.2,zorder=0)
    axes[0].legend(ncol=4,frameon=False,loc='upper center',bbox_to_anchor=(.5,1.35),fontsize=8)
    axes[1].set_xticks(x,[nice_c[c].replace(' ','\n') for c in conditions])
    fig.text(.02,.01,'64 fixed questions per condition. Exact duplicate requests reuse a saved response. Automatic numerical scoring.',fontsize=8,color='#444444')
    fig.tight_layout(rect=[0,.03,1,.97])
    fig.savefig(figures/'generative_outcomes.png',dpi=240)
    fig.savefig(figures/'generative_outcomes.pdf')
    plt.close(fig)
    print('Manuscript words:',len(template.split()))
    print('Figure and manuscript written.')


if __name__=='__main__':main()
