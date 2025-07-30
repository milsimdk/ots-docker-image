#!/usr/bin/env python3
import os, yaml, shutil, string;
from opentakserver.defaultconfig import DefaultConfig;
from flask.config import Config as FlaskConfig;

config_file = os.path.join( os.environ.get("DOCKER_OTS_DATA_FOLDER", "/app/ots/"), "config.yml" );

#************ HELPERS ************
def save_config(config):
    global config_file
    try:
        with open(config_file, "w") as config_file:
            yaml.safe_dump(dict(config), config_file)
            logger("Container init | Saving config file...")
    except BaseException as e:
        logger("Container init | Failed to save config.yml: {}".format(e))

def mediamtx_config_init(config):
    # Try to set the MediaMTX token
    if is_true(config.get("OTS_MEDIAMTX_ENABLE", False)):
        try:
            mediamtx_config_template    = os.path.join(config.get("OTS_DATA_FOLDER", "/app/ots/"), "mediamtx", "mediamtx.template")
            mediamtx_config_file        = os.path.join(config.get("OTS_DATA_FOLDER", "/app/ots/"), "mediamtx", "mediamtx.yml")

            # Do the mediamtx.* files exists ?
            # Do we exists :O
            if not os.path.isfile(mediamtx_config_file) and os.path.isfile(mediamtx_config_template):
                # Copy mediamtx template to config file
                shutil.copyfile( mediamtx_config_template, mediamtx_config_file )
                # Update MediaMTX token
                with open(mediamtx_config_file, "r") as mediamtx_config:
                    conf = mediamtx_config.read()
                    conf = conf.replace("MTX_TOKEN", config.get("OTS_MEDIAMTX_TOKEN"))
                with open(mediamtx_config_file, "w") as mediamtx_config:
                    mediamtx_config.write(conf)
                logger("Container init | Generating MediaMTX config")
                logger("Container init | MediaMTX enabled")
            else:
                logger("Container init | MediaMTX enabled")
        except BaseException as e:
            logger("Container init | Failed to set MediaMTX token: {}".format(e))
    else:
        logger("Container init | MediaMTX disabled")

def is_true(value):
    return str(value).strip().lower() in {"true", "yes", "1", "on", "enable", "enabled"} if not isinstance(value, bool) else value

def logger(value):
    CEND  = '\033[0m'
    INFO  = '\033[32m'
    WARN  = '\033[33m'
    ERROR = '\033[31m'
    CYAN  = '\033[36m'
    PURPLE = '\033[35m'
    BLUE  = '\033[34m'
    print(BLUE + value + CEND)

#************ INIT ************
# Get config file,
# Load config.yml if it exists
if not os.path.exists(config_file) or is_true(os.environ.get("DEV_CONFIG_OVERWRITE", False)):
    logger("Container init | Creating config.yml")

    # Get default config from opentakserver
    config = FlaskConfig(config_file);
    config.from_object(DefaultConfig);

    # Get env variables with the prefix 'DOCKER_'
    # Used so we can override variables from the docker-compose file
    config.from_prefixed_env('DOCKER', loads=yaml.safe_load);

    # Override settings to make OTS work in a container
    config.update(
        OTS_LISTENER_ADDRESS        = os.environ.get("DOCKER_OTS_LISTENER_ADDRESS", "0.0.0.0"),
        OTS_RABBITMQ_SERVER_ADDRESS = os.environ.get("DOCKER_OTS_RABBITMQ_SERVER_ADDRESS", "rabbitmq"),
        OTS_MEDIAMTX_API_ADDRESS    = os.environ.get("DOCKER_OTS_MEDIAMTX_API_ADDRESS", "http://mediamtx:9997"),
        SECURITY_TOTP_ISSUER        = config.get("OTS_CA_ORGANIZATION", "OpenTAKServer"),
        OTS_CA_SUBJECT              = '/C={}/ST={}/L={}/O={}/OU={}'.format(
            config.get("OTS_CA_COUNTRY", "WW"),
            config.get("OTS_CA_STATE", "XX"),
            config.get("OTS_CA_CITY", "YY"),
            config.get("OTS_CA_ORGANIZATION", "ZZ"),
            config.get("OTS_CA_ORGANIZATIONAL_UNIT", "OpenTAKServer")
        )
    )

    # Check if MediaMTX is enabled, if so fix the config for MediaMTX
    mediamtx_config_init(config)
    save_config(config)
else:
    logger('Container init | Found existing config.yml')
    logger('Container init | Checking environment variables...')

    # Get config.yml
    init_config_file = FlaskConfig(config_file)
    init_config_file.from_file(config_file, load=yaml.safe_load);

    # Get Docker Env
    init_config_env = FlaskConfig(config_file)
    init_config_env.from_prefixed_env('DOCKER', loads=yaml.safe_load);

    # Compare config.yml and docker env.
    init_config_diff = set(init_config_file).intersection(set(init_config_env))

    # If there is a differnce between the two, update config.yml with the new docker env.
    if bool(init_config_diff):
        init_config_updated = dict()
        for value in init_config_diff:
            if init_config_file[value] != init_config_env[value]:
                logger("Container init | Found changed environment variable ['{}'] old value: '{}' new value: '{}'".format(value, init_config_file[value], init_config_env[value]))
                init_config_updated[value] = init_config_env[value]

        if bool(init_config_updated):
            init_config_file.update(init_config_updated)
            # Check if MediaMTX is enabled, if so fix the config for MediaMTX
            save_config(init_config_file)
        else:
            logger('Container init | No changed environment variables found')
        mediamtx_config_init(init_config_file)

# Start the OpenTAKServer app
logger('Container init | Starting OpenTAKServer...')
