from trustllm_trove.warc_with_meta import WarcReader
from trustllm_trove.html_extractor import HTMLExtractor, HTMLFilter
from trustllm_trove.signals import PreFilter, RepetitionFilter
from trustllm_trove.c4 import C4QualityFilter
from datatrove.io import DataFolder
from datatrove.executor import (
        SlurmPipelineExecutor,
        LocalPipelineExecutor
        )
from datatrove.pipeline.dedup import MinhashDedupCluster, MinhashDedupFilter, MinhashDedupSignature
from datatrove.pipeline.writers.jsonl import JsonlWriter
from datatrove.pipeline.filters import (
    LanguageFilter,
    URLFilter,
)

DUMP = 'CC-MAIN-2023-50'
INPATH = f'/p/data1/datasets/CommonCrawl/{DUMP}'
OUTPATH = f'/p/scratch/trustllm-eu/WP2/CC/{DUMP}/out'
LOGPATH = f'/p/scratch/trustllm-eu/WP2/CC/{DUMP}/log'

def exclusion_writer(name):
    return JsonlWriter(f'{OUTPATH}/removed/{name}')

LANGSET = [
    'eng', # English
    'ang', # Old English
    'sco', # Scots
    'deu', # German
    'gsw', # Swiss German
    'swg', # Swabian
    'ksh', # Kölsch
    'nds', # Low German
    'bar', # Bavarian
    'stq', # Saterfriesisch
    'gos', # Gronings
    'hrx', # Hunsrik
    'pdc', # Pennsylvania German
    'pfl', # Pfaelzisch
    'prg', # Prussian
    'got', # Gothic
    'gmh', # Middle High German
    'nld', # Dutch
    'afr', # Afrikaans
    'fry', # Western Frisian
    'frr', # Northern Frisian
    'ltz', # Luxembourgish
    'vls', # Vlaams
    'lim', # Limburgish
    'zea', # Zeelandic
    'swe', # Swedish
    'dan', # Danish
    'nno', # Norwegian (Nynorsk)
    'nob', # Norwegian (Bokmål)
    'isl', # Icelandic
    'fao', # Faroese
    'non', # Old Norse
    ]

pipeline = [
        WarcReader(
            DataFolder(INPATH),
            glob_pattern='**/*warc.gz',
            recursive=True,
            min_length=512,
            ),
        URLFilter(exclusion_writer=exclusion_writer('url')),
        HTMLFilter(), #This is not a filter, it just adds html metadata tags that are removed by text extraction.
        HTMLExtractor(),
        PreFilter(exclusion_writer=exclusion_writer('prefilter')),
        LanguageFilter(
            exclusion_writer=exclusion_writer('language'),
            languages = [f'{l}_Latn' for l in LANGSET],
            backend='glotlid',
            language_threshold=.4
            ),
        RepetitionFilter(exclusion_writer=exclusion_writer('repetition')),
        C4QualityFilter(
            filter_no_terminal_punct=False,
            filter_curly_bracket=False,
            filter_javascript=False,
            exclusion_writer=exclusion_writer('c4'),
            ),
        JsonlWriter(OUTPATH),
        ]

#executor = LocalPipelineExecutor(
#        pipeline=pipeline,
#        tasks=1,
#        logging_dir=LOGPATH,
#        workers=1,
#        )

executor = SlurmPipelineExecutor(
    pipeline=pipeline,
    logging_dir=LOGPATH,
    tasks=2,
    cpus_per_task=48,
    mem_per_cpu_gb=96,
    job_name='datatrove-trustllm',
    partition='batch',
    time='24:00:00',
    sbatch_args = {'account': 'trustllm-eu'},
    requeue=False,
)

if __name__ == '__main__':
    executor.run()
