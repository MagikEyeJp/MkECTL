# -*- coding: utf-8 -*-

import os
from .bus import TcpBus, SerialBus, DefaultBus
from .api import *
from .sync_client import SyncClient

init_dir = os.path.dirname(os.path.realpath(__file__))

reapi_path = os.path.join(init_dir, 'reserved_sync_client.py')
if os.path.exists(reapi_path):
    from .reserved_sync_client import ReservedSyncClient
    from .reserved_api import *

srv_path = os.path.join(init_dir, 'tcp_server.py')
if os.path.exists(srv_path):
    from .tcp_server import TcpServer
