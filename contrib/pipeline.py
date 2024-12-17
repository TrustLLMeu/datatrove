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
import argparse


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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_data_dir", type=str)
    parser.add_argument("--output_path", type=str)
    parser.add_argument("--total_tasks", type=int, default=400)
    parser.add_argument("--local_tasks", type=int, default=100)
    parser.add_argument("--local_rank_offset", type=int, default=0)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    INPATH = args.input_data_dir
    OUTPATH = args.output_path

    pipeline = [
            WarcReader(
                DataFolder(args.input_data_dir),
                glob_pattern='**/*warc.gz',
                recursive=True,
                min_length=512,
                ),
            # URLFilter(), SKIP THIS: TLDEXTRACT 
            HTMLFilter(), #This is not a filter, it just adds html metadata tags that are removed by text extraction.
            HTMLExtractor(),
            PreFilter(),
            LanguageFilter(
                languages = [f'{l}_Latn' for l in LANGSET],
                backend='glotlid',
                language_threshold=.4
                ),
            RepetitionFilter(),
            C4QualityFilter(
                filter_no_terminal_punct=False,
                filter_curly_bracket=False,
                filter_javascript=False,
                ),
            JsonlWriter(f'{OUTPATH}/data'),
            ]

    executor = LocalPipelineExecutor(
            pipeline=pipeline,
            tasks=args.total_tasks,
            local_tasks=args.local_tasks,
            local_rank_offset=args.local_rank_offset,
            workers=args.workers,
            logging_dir=f'{OUTPATH}/logs'
            )
    executor.run()
