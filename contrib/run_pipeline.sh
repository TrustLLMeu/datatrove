#!/bin/bash
#SBATCH --time 12:00:00
#SBATCH --array=0-29
#SBATCH --partition=batch
#SBATCH --ntasks=1             # number of tasks per array task?
#SBATCH --cpus-per-task=48     # number of cpus per task.
#SBATCH --job-name=CC-pipeline
#SBATCH --account=trustllm-eu
#SBATCH --output=logs/slurm_%j.out
#SBATCH --error=logs/slurm_%j.err

set -xe

# Set env vars
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}
echo "OMP_NUM_THREADS=$OMP_NUM_THREADS"
export PYTHONUNBUFFERED=TRUE

# MAKE SURE THESE POINT TO THE RIGHT PLACE! 
source /p/project1/trustllm-eu/cubagyllensten1/envs/ccproc/bin/activate

TLDEXTRACT_CACHE="/p/project1/trustllm-eu/cubagyllensten1/datatrove/contrib/tldextract.cache"

TOTAL_TASKS=3000
LOCAL_TASKS=100
WORKERS=50
# Multiply $SLURM_ARRAY_TASK_ID by $LOCAL_TASKS to get the starting task
LOCAL_RANK_OFFSET=$((SLURM_ARRAY_TASK_ID * LOCAL_TASKS))

DATA_DIR="/p/data1/datasets/CommonCrawl/CC-MAIN-2023-23"
OUTPUT_PATH="/p/data1/trustllmd/wp2/CC"

python pipeline.py --input_data_dir $DATA_DIR --output_path $OUTPUT_PATH --total_tasks $TOTAL_TASKS --local_tasks $LOCAL_TASKS --local_rank_offset $LOCAL_RANK_OFFSET --workers $WORKERS
