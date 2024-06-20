#!/usr/bin/env python3
import os, yaml;
from opentakserver.defaultconfig import DefaultConfig;
from flask.config import Config as FlaskConfig;

config_file = os.path.join( os.environ.get("DOCKER_OTS_DATA_FOLDER", "/app/ots/"), "config.yml" );
config = FlaskConfig(config_file);

#************ HELPERS ************
def save_config(config):
    global config_file
    try:
        with open(config_file, "w") as config_file:
            yaml.safe_dump(dict(config), config_file)
            print("Container init | Saving config file...")
    except BaseException as e:
        print("Container init | Failed to save config.yml: {}".format(e))

#************ INIT ************
# Get config file,
# Load config.yml if it exists
if not os.path.exists(config_file) or bool( yaml.safe_load( os.environ.get("DEV_CONFIG_OVERWRITE", False) ) ):
    print("Container init | Creating config.yml")

    # Get default config from opentakserver
    config.from_object(DefaultConfig);

    # Get env variables with the prefix 'DOCKER_'
    # Used so we can override variables from the docker-compose file
    config.from_prefixed_env('DOCKER');

    # Override settings to make OTS work in a container
    config.update(
        OTS_LISTENER_ADDRESS = os.environ.get("DOCKER_OTS_LISTENER_ADDRESS", "0.0.0.0"),
        OTS_RABBITMQ_SERVER_ADDRESS = os.environ.get("DOCKER_OTS_RABBITMQ_SERVER_ADDRESS", "rabbitmq"),
        OTS_CA_SUBJECT = '/C={}/ST={}/L={}/O={}/OU={}'.format( config["OTS_CA_COUNTRY"], config["OTS_CA_STATE"], config["OTS_CA_CITY"], config["OTS_CA_ORGANIZATION"], config["OTS_CA_ORGANIZATIONAL_UNIT"] ),
        SECURITY_TOTP_ISSUER = config["OTS_CA_ORGANIZATION"]
    )

    save_config(config)
else:
    print('Container init | Found existing config.yml')
    print('Container init | Checking environment variables...')

    # Get config.yml
    init_config_file = FlaskConfig(config_file)
    init_config_file.from_file(config_file, load=yaml.safe_load);

    # Get Docker Env
    init_config_env = FlaskConfig(config_file)
    init_config_env.from_prefixed_env('DOCKER');

    # Compare config.yml and docker env.
    init_config_diff = set(init_config_file).intersection(set(init_config_env))

    # If there is a differnce between the two, update config.yml with the new docker env.
    if bool(init_config_diff):
        init_config_updated = dict()
        for value in init_config_diff:
            if init_config_file[value] != init_config_env[value]:
                print("Container init | Found changed environment variable ['{}'] old value: '{}' new value: '{}'".format(value, init_config_file[value], init_config_env[value]))
                init_config_updated[value] = init_config_env[value]

        if bool(init_config_updated):
            init_config_file.update(init_config_updated)
            save_config(init_config_file)
        else:
            print('Container init | No changed environment variables found')

# Start the OpenTAKServer app
print('Container init | Starting OpenTAKServer...')
