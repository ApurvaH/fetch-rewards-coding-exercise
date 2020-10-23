import datetime
import logging
import sys
from typing import List
import yaml

import boto3

from models import Server, Volume
from validation import validate_server

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
ec2_client = boto3.client('ec2')


def load_specifications(location):
    with open(location) as file:
        for specification in yaml.load_all(file, yaml.SafeLoader):
            yield specification


def choose_image(ami_type, architecture, root_device_type, virtualization_type):
    images_response = ec2_client.describe_images(
        Owners=["amazon"],
        Filters=[
            {"Name": "name", "Values": ["{}*".format(ami_type)]},
            {"Name": "architecture", "Values": [architecture]},
            {"Name": "root-device-type", "Values": [root_device_type]},
            {"Name": "virtualization-type", "Values": [virtualization_type]}
        ]
    )
    images = images_response.get('Images')
    images.sort(key=lambda im: im.get('CreationDate'), reverse=True)
    return images[0]


def to_block_device_mapping(volumes: List[Volume]):
    root_device_name = None
    block_device_mappings = []
    for volume in volumes:
        if volume.mount == "/":
            if root_device_name is None:
                root_device_name = volume.device
            else:
                raise Exception("There can only be one Root Device getting mapped to '/'")
        block_device_mappings.append({
            "DeviceName": volume.device,
            "Ebs": {
                "VolumeSize": volume.size_gb,
                "VolumeType": "standard"
            },
        })
    return root_device_name, block_device_mappings


def generate_cloud_init_script(server: Server, root_device_name):
    script = \
        '''
        #!/usr/bin/env sh
         
        '''

    for volume in server.volumes:
        # Root volume will already be setup by the operating system
        if volume.device != root_device_name:
            script += \
                f'''
                 mkfs -t {volume.type} {volume.device}
                 mkdir -p {volume.mount}
                 mount {volume.device} {volume.mount} -o rw
                 chmod 777 {volume.mount}
                 '''

    for user in server.users:
        script += \
            f'''
             id -u {user.login} || useradd -m {user.login}
             mkdir -p /home/{user.login}/.ssh/
             echo "{user.ssh_key}" >> /home/{user.login}/.ssh/authorized_keys
             chown -R {user.login} /home/{user.login}/
             '''

    return script


def deploy_and_setup_server(server: Server):
    deployer_tag = "deployer-{}".format(datetime.datetime.now().isoformat())
    logging.info("Creating Instances with Deployer Tag %s", deployer_tag)

    root_device_name, block_device_mappings = to_block_device_mapping(server.volumes)
    logging.info("Will create %d block devices", len(block_device_mappings))

    image = choose_image(server.ami_type, server.architecture, server.root_device_type, server.virtualization_type)

    try:
        logging.info("Lunching Instances")
        ec2_client.run_instances(
            InstanceType=server.instance_type,
            ImageId=image["ImageId"],
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [{"Key": "Deployer", "Value": deployer_tag}]
            }],
            UserData=generate_cloud_init_script(server, root_device_name),
            MinCount=server.min_count,
            MaxCount=server.max_count,
            BlockDeviceMappings=block_device_mappings)
    except Exception as e:
        raise e


def main():
    if len(sys.argv) != 2:
        print("""Usage: python3 deployer.py /path/to/file.yaml""")
        return
    servers = []
    spec_filename = sys.argv[1]

    for specification in load_specifications(spec_filename):
        server_mapping = specification["server"]
        validate_server(server_mapping)
        servers.append(Server.from_dict(specification["server"]))

    for server in servers:
        deploy_and_setup_server(server)


if __name__ == '__main__':
    main()
