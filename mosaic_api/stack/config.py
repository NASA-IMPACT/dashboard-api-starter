"""STACK Configs."""

import os
import yaml

config = yaml.load(open('stack/config.yml', 'r'), Loader=yaml.FullLoader)

PROJECT_NAME = config['PROJECT_NAME']
STAGE = config.get('STAGE') or 'dev'

# Additional environement variable to set in the task/lambda
TASK_ENV: dict = dict()

# Existing VPC to point ECS/LAMBDA stacks towards. Defaults to creating a new
# VPC if no ID is supplied.
VPC_ID = os.environ.get("VPC_ID") or config['VPC_ID']

################################################################################
#                                                                              #
#                                 LAMBDA                                       #
#                                                                              #
################################################################################
TIMEOUT: int = config['TIMEOUT']
MEMORY: int = config['MEMORY']

# stack skips setting concurrency if this value is 0
# the stack will instead use unreserved lambda concurrency
MAX_CONCURRENT: int = 500 if STAGE == "prod" else config['MAX_CONCURRENT']
