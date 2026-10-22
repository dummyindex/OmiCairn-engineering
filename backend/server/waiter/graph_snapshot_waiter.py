from constants.sss import (
    GRAPH_SNAPSHOT_IMAGE_PREFIX,
    GRAPH_SNAPSHOT_ENVIRONMENT_PREFIX,
)
from sss.porter_factory import PorterFactory


class GraphSnapshotImageWaiter:
    def __init__(self, snapshot_uuid) -> None:
        self.porter = PorterFactory.create_porter()
        self.snapshot_uuid = snapshot_uuid
        self.object_key = f"{GRAPH_SNAPSHOT_IMAGE_PREFIX}/{snapshot_uuid}.png"
        self.porter.set_operation_target(self.object_key)

    def check_file(self):
        return self.porter.check_file()


class GraphSnapshotEnvironmentWaiter:
    def __init__(self, snapshot_uuid) -> None:
        self.porter = PorterFactory.create_porter()
        self.snapshot_uuid = snapshot_uuid
        self.object_key = f"{GRAPH_SNAPSHOT_ENVIRONMENT_PREFIX}/{snapshot_uuid}"
        self.porter.set_operation_target(self.object_key)

    def check_file(self):
        return self.porter.check_file()
