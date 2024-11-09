#!/bin/bash
#SBATCH --time 12:00:00
#SBATCH --array=0-29
#SBATCH --partition=batch
#SBATCH --job-name=data_quality_analysis
#SBATCH --account=trustllm-eu

set -xe

# Set env vars
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
echo "OMP_NUM_THREADS=$OMP_NUM_THREADS"
export PYTHONUNBUFFERED=TRUE


source processingvenv/bin/activate

TOTAL_TASKS=3000
LOCAL_TASKS=100
WORKERS=50
# Multiply $SLURM_ARRAY_TASK_ID by $LOCAL_TASKS to get the starting task
LOCAL_RANK_OFFSET=$((SLURM_ARRAY_TASK_ID * LOCAL_TASKS))

DATA_DIR="/p/data1/trustllmd/WP2/data/final"
OUTPUT_PATH="/p/data1/trustllmd/ingvarssonjuto1/data_quality_labels/output_new_run"


python trustllm/datatrove/examples/fineweb_label_trustllm.py --input_data_dir $DATA_DIR --output_path $OUTPUT_PATH --total_tasks $TOTAL_TASKS --local_tasks $LOCAL_TASKS --local_rank_offset $LOCAL_RANK_OFFSET --workers $WORKERS
