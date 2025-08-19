#!/bin/bash
source /Users/tharundchowdary/miniforge3/etc/profile.d/conda.sh
conda activate base
export EXA_API_KEY="29966140-48f9-4786-8c70-fd539db903be"
cd /Users/tharundchowdary/exa-mcp-server-klavis
python server.py
