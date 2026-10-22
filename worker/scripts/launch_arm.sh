OMICAIRN_CODE_SPACE="${OMICAIRN_CODE_SPACE:-/omicairn/code_space}"
source $OMICAIRN_CODE_SPACE/scripts/set-env-variables.sh
source $OMICAIRN_CODE_SPACE/scripts/set-local-env-variables.sh
# bash $OMICAIRN_CODE_SPACE/scripts/install-dependencies.sh
cd $OMICAIRN_CODE_SPACE/daemon
nohup python3 scan_timeout_computations.py > scan-timeout-computation-output.log 2>&1 &
nohup python3 queue_job.py > queue-job-output.log 2>&1 &
nohup python3 refresh_fb_avg_duration.py > refresh-fb-avg-duration-output.log 2>&1 &
# nohup python3 statistic_fb_version_consumption.py > statistic-fb-version-consumption-output.log 2>&1 &
cd $OMICAIRN_CODE_SPACE/server
# Increase timeout to 600s (10 min) to handle long-running LLM requests
# Previous 120s was too short, causing frequent worker timeouts
gunicorn -w 6 -b 0.0.0.0:80 --timeout 600 --log-level info main:app