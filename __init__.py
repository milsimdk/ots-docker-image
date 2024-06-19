#!/usr/bin/env python3
import os, yaml, subprocess;
from opentakserver.defaultconfig import DefaultConfig;
from flask.config import Config as FlaskConfig;

config_file = os.path.join( os.environ.get("DOCKER_OTS_DATA_FOLDER", "/app/ots/"), "config.yml" );
config = FlaskConfig(config_file);

def save_config(config):
    global config_file
    try:
        with open(config_file, "w") as config_file:
            yaml.safe_dump(dict(config), config_file)
            print("Container init | Saving config file...")
    except BaseException as e:
        print("Container init | Failed to save config.yml: {}".format(e))

# Get config file,
# Load config.yml if it exists
if not os.path.exists(config_file) or os.environ.get("DOCKER_CONFIG_OVERWRITE", False):
    print("Container init | Creating config.yml")

    # Get default config from opentakserver
    config.from_object(DefaultConfig);

    # Override settings to make OTS work in a container
    config.update(
        OTS_LISTENER_ADDRESS = os.environ.get("DOCKER_OTS_LISTENER_ADDRESS", "0.0.0.0"),
        OTS_RABBITMQ_SERVER_ADDRESS = os.environ.get("DOCKER_OTS_RABBITMQ_SERVER_ADDRESS", "rabbitmq")
    )

    # Get env variables with the prefix 'DOCKER_'
    # Used so we can override variables from the docker-compose file
    config.from_prefixed_env('DOCKER');

    save_config(config)
else:
    print('Container init | Found existing config.yml')

    print('Container init | Checking environment variables...')
    init_config_file = FlaskConfig(config_file)
    init_config_file.from_file(config_file, load=yaml.safe_load);

    init_config_env = FlaskConfig(config_file)
    init_config_env.from_prefixed_env('DOCKER');

    init_config_diff = set(init_config_file).intersection(set(init_config_env))

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
ots = subprocess.Popen( ['python3', '-m', 'opentakserver.app'], start_new_session=True)
ots.wait()
