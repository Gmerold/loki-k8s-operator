#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""Config builder for Loki Charmed Operator."""

import os

# Paths in workload container
HTTP_LISTEN_PORT = 3100
LOKI_CONFIG_DIR = "/etc/loki"
LOKI_CONFIG = os.path.join(LOKI_CONFIG_DIR, "loki-local-config.yaml")
LOKI_CERTS_DIR = os.path.join(LOKI_CONFIG_DIR, "certs")

CERT_FILE = os.path.join(LOKI_CERTS_DIR, "loki.cert.pem")
KEY_FILE = os.path.join(LOKI_CERTS_DIR, "loki.key.pem")

LOKI_DIR = "/loki"
CHUNKS_DIR = os.path.join(LOKI_DIR, "chunks")
BOLTDB_DIR = os.path.join(LOKI_DIR, "boltdb-shipper-active")
RULES_DIR = os.path.join(LOKI_DIR, "rules")


class ConfigBuilder:
    """Loki configuration builder class.

    Some minimal configuration is required for Loki to start, including: storage paths, schema,
    ring.

    Reference: https://grafana.com/docs/loki/latest/configuration/
    """

    _target: str = "all"
    _auth_enabled: bool = False

    def __init__(
        self, instance_addr: str, alertmanager_url: str, external_url: str, http_tls: bool = False
    ):
        """Init method."""
        self.instance_addr = instance_addr
        self.alertmanager_url = alertmanager_url
        self.external_url = external_url
        self.http_tls = http_tls

    def build(self) -> dict:
        """Build Loki config dictionary."""
        return {
            "target": self._target,
            "auth_enabled": self._auth_enabled,
            "common": self._common,
            "ingester": self._ingester,
            "ruler": self._ruler,
            "schema_config": self._schema_config,
            "server": self._server,
            "storage_config": self._storage_config,
        }

    @property
    def _common(self) -> dict:
        return {
            "path_prefix": LOKI_DIR,
            "replication_factor": 1,
            "ring": {"instance_addr": self.instance_addr, "kvstore": {"store": "inmemory"}},
            "storage": {
                "filesystem": {
                    "chunks_directory": CHUNKS_DIR,
                    "rules_directory": RULES_DIR,
                }
            },
        }

    @property
    def _ingester(self) -> dict:
        return {
            "wal": {
                "dir": os.path.join(CHUNKS_DIR, "wal"),
                "enabled": True,
                "flush_on_shutdown": True,
            }
        }

    @property
    def _ruler(self) -> dict:
        # Reference: https://grafana.com/docs/loki/latest/configure/#ruler
        return {
            "alertmanager_url": self.alertmanager_url,
            "external_url": self.external_url,
        }

    @property
    def _schema_config(self) -> dict:
        return {
            "configs": [
                {
                    "from": "2020-10-24",
                    "index": {"period": "24h", "prefix": "index_"},
                    "object_store": "filesystem",
                    "schema": "v11",
                    "store": "boltdb",
                }
            ]
        }

    @property
    def _server(self) -> dict:
        _server = {
            "http_listen_address": "0.0.0.0",
            "http_listen_port": HTTP_LISTEN_PORT,
        }

        if self.http_tls:
            _server["http_tls_config"] = {
                "cert_file": CERT_FILE,  # HTTP server cert path.
                "key_file": KEY_FILE,  # HTTP server key path.
            }

        return _server

    @property
    def _storage_config(self) -> dict:
        return {
            "boltdb": {"directory": BOLTDB_DIR},
            "filesystem": {"directory": CHUNKS_DIR},
        }
