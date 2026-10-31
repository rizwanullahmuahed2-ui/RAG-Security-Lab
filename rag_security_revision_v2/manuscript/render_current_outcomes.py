"""Render the current manuscript figure from unchanged saved result summaries.

The frozen analysis and its original exports remain untouched. Only the
presentation footer is updated for the current source-based case-analysis scope.
"""
import hashlib
import json
import os
from pathlib import Path

def build_figure(summary, n_questions, rounds, output):
    metrics = ['strict_reference_choice_proxy', 'strict_target_choice_proxy']
    conditions = ['clean', 'targeted', 'unrelated', 'benign', 'accepted_label']
    defenses = ['none', 'rerank', 'filter', 'filter_rerank']
    lookup = {(row['condition'], row['defense'], row['metric']): row for row in summary if row['module'] == 'core'}
    if any((condition, defense, metric) not in lookup or lookup[(condition, defense, metric)]['mean_question_rate'] is None
           for condition in conditions for defense in defenses for metric in metrics):
        return {'status': 'withheld_primary_core_grid_incomplete'}
    os.environ.setdefault('MPLCONFIGDIR', '/tmp/rag-current-figure-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.spines.top': False, 'axes.spines.right': False})
    colors = ['#173f5f', '#ed8b24', '#278779', '#985aa1']
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 6.8), sharex=True)
    labels = {'none': 'None', 'rerank': 'Rerank', 'filter': 'Filter', 'filter_rerank': 'Filter + rerank'}
    x, width = np.arange(len(conditions)), .18
    for ax, metric in zip(axes, metrics):
        for index, (defense, color) in enumerate(zip(defenses, colors)):
            records = [lookup[(condition, defense, metric)] for condition in conditions]
            means = np.array([row['mean_question_rate']*100 for row in records])
            low = np.array([row['round_rate_min']*100 for row in records])
            high = np.array([row['round_rate_max']*100 for row in records])
            ax.bar(x+(index-1.5)*width, means, width, label=labels[defense], color=color,
                   yerr=np.array([np.maximum(0, means-low), np.maximum(0, high-means)]),
                   capsize=2, zorder=3)
        ax.set_ylim(0, 108); ax.set_ylabel('Questions (%)')
        ax.set_title('Strict reference-choice proxy' if 'reference' in metric else 'Strict target-choice proxy', loc='left')
        ax.grid(axis='y', alpha=.2, zorder=0)
    axes[0].legend(ncol=4, frameon=False, loc='upper center', bbox_to_anchor=(.5, 1.25))
    axes[1].set_xticks(x, ['Clean', 'Targeted', 'Unrelated', 'Benign', 'Accepted\nlabel'])
    fig.text(.02, .01, f'{n_questions} fixed questions; {rounds} fresh rounds per distinct payload. Ranges span rounds. Automatic proxies; semantic case analysis reported separately.', fontsize=8)
    fig.tight_layout(rect=[0, .035, 1, .98])
    for suffix in ['png', 'pdf']:
        fig.savefig(output / ('study_c_outcomes.'+suffix), dpi=240, bbox_inches='tight')
    plt.close(fig)
    return {'status': 'created_from_saved_outputs', 'png': 'study_c_outcomes.png', 'pdf': 'study_c_outcomes.pdf',
            'error_bars': 'Minimum and maximum observed round rates, not confidence intervals'}

def render_current_outcomes(work, output):
    source=work/'analysis/study_c/analysis.json'
    report=json.loads(source.read_text())
    result=build_figure(report['summary'],report['execution']['questions'],report['execution']['rounds'],output)
    assert result['status']=='created_from_saved_outputs'
    provenance={'source_analysis_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'change':'Presentation footer updated; saved metrics and archived analysis exports unchanged.',
                'files':{f'study_c_outcomes.{ext}':hashlib.sha256((output/f'study_c_outcomes.{ext}').read_bytes()).hexdigest()for ext in ['png','pdf']}}
    (output/'CURRENT_FIGURE_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
