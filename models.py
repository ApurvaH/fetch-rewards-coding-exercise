class Volume(object):
    def __init__(self, device, size_gb, type, mount):
        self.device = device
        self.size_gb = size_gb
        self.type = type
        self.mount = mount

    @staticmethod
    def from_dict(mapping):
        return Volume(
            mapping.get("device"),
            mapping.get("size_gb"),
            mapping.get("type"),
            mapping.get("mount"))


class User(object):
    def __init__(self, login, ssh_key):
        self.login = login
        self.ssh_key = ssh_key

    @staticmethod
    def from_dict(mapping):
        return User(
            mapping.get("login"),
            mapping.get("ssh_key"))


class Server(object):
    def __init__(self,
                 instance_type, ami_type, architecture, root_device_type, virtualization_type, min_count, max_count,
                 volumes, users):
        self.instance_type = instance_type
        self.ami_type = ami_type
        self.architecture = architecture
        self.root_device_type = root_device_type
        self.virtualization_type = virtualization_type
        self.min_count = min_count
        self.max_count = max_count
        self.volumes = volumes
        self.users = users

    @staticmethod
    def from_dict(mapping):
        return Server(
            mapping.get("instance_type"),
            mapping.get("ami_type"),
            mapping.get("architecture"),
            mapping.get("root_device_type"),
            mapping.get("virtualization_type"),
            mapping.get("min_count"),
            mapping.get("max_count"),
            [Volume.from_dict(volume) for volume in mapping.get("volumes")],
            [User.from_dict(user) for user in mapping.get("users")])
