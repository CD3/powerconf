#! /bin/bash
cd /home/cclark/Code/sync/projects/powerconf/doc/examples/cli/running_external_models_with_run_command/acme/acme-workspace
set -e
mkdir -p /home/cclark/Code/sync/projects/powerconf/doc/examples/cli/running_external_models_with_run_command/acme/acme-workspace/output
cd /home/cclark/Code/sync/projects/powerconf/doc/examples/cli/running_external_models_with_run_command/acme/acme-workspace/output
python ../../acme ../config_files/ACME-solver-2_micrometer.ini > acme.stdout
mkdir -p /home/cclark/Code/sync/projects/powerconf/doc/examples/cli/running_external_models_with_run_command/acme/acme-workspace
cd /home/cclark/Code/sync/projects/powerconf/doc/examples/cli/running_external_models_with_run_command/acme/acme-workspace
echo "DONE"