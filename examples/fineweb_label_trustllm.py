import os
from argparse import ArgumentParser

from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.filters import (
    C4QualityFilter,
    FineWebQualityFilter,
    GopherQualityFilter,
    GopherRepetitionFilter,
    LanguageFilter,
)
from datatrove.pipeline.readers import ParquetReader
from datatrove.pipeline.writers.parquet import ParquetWriter


def run_labelling_pipeline(
    input_data_dir: str, output_path: str, total_tasks: int, local_tasks: int, local_rank_offset: int, workers: int
):
    main_processing_executor = LocalPipelineExecutor(
        pipeline=[
            ParquetReader(
                input_data_dir,
                glob_pattern="*/*.parquet",
            ),
            LanguageFilter(label_only=True, backend="glotlid"),
            GopherRepetitionFilter(label_only=True),
            GopherQualityFilter(label_only=True),
            # C4QualityFilter(filter_no_terminal_punct=False),
            FineWebQualityFilter(label_only=True),
            ParquetWriter(
                os.path.join(output_path, "data"),
                output_filename="${lang}/${rank}.parquet",
                compression="snappy",
                max_file_size=1 * 2**30,
                expand_metadata=True,
            ),
        ],
        tasks=total_tasks,
        local_tasks=local_tasks,
        local_rank_offset=local_rank_offset,
        workers=workers,
        logging_dir=os.path.join(output_path, "logs"),
    )

    main_processing_executor.run()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input_data_dir", type=str)
    parser.add_argument("--output_path", type=str)
    parser.add_argument("--total_tasks", type=int, default=400)
    parser.add_argument("--local_tasks", type=int, default=100)
    parser.add_argument("--local_rank_offset", type=int, default=0)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    run_labelling_pipeline(
        args.input_data_dir,
        args.output_path,
        args.total_tasks,
        args.local_tasks,
        args.local_rank_offset,
        args.workers,
    )
