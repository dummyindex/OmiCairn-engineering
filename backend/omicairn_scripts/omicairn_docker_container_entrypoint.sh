export PROJECT_ROOT="${PROJECT_ROOT:-/omicairn_root}"
bash "$PROJECT_ROOT/omicairn_scripts/omicairn_prepare-store.sh"
source "$PROJECT_ROOT/omicairn_scripts/omicairn_set-env-variables.sh"
# Deployment-specific settings (database, object storage, service hosts).
# Copy omicairn_set-local-env-variables.sh and adapt it, or pass variables via `docker run --env-file .env`.
source "$PROJECT_ROOT/omicairn_scripts/omicairn_set-local-env-variables.sh"
cd $PROJECT_ROOT/server/
gunicorn -w 2 --timeout 600 -b 0.0.0.0:80 "main:create_app()"
