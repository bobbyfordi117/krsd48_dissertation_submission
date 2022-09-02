#!/bin/bash
#SBATCH -N 1
#SBATCH -c 4
#SBATCH --gres=gpu
#SBATCH -p tpg-gpu-small
#SBATCH --qos=short
#SBATCH --job-name=testing_ML
#SBATCH -t 07:00:00
#SBATCH --mail-type=END
#SBATCH --mail-user krsd48@durham.ac.uk

# Source the bash profile (required to use the module command)
source /etc/profile
module load cuda/8.0

# Run your program (replace this with your program)
srun jupyter nbconvert --to notebook --execute mel_non_aug.ipynb