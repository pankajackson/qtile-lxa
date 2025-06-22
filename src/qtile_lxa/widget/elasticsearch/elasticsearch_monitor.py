import webbrowser
from elasticsearch import Elasticsearch as ES
from qtile_extras.widget import GenPollText
from libqtile.log_utils import logger
from .typing import ElasticsearchMonitorConfig
from typing import Any


class ElasticsearchMonitor(GenPollText):
    def __init__(self, config: ElasticsearchMonitorConfig, **kwargs: Any) -> None:
        self.config = config
        self.format = "{symbol} {label}"
        super().__init__(func=self.safe_status_poll, **kwargs)

    def log_errors(self, msg: str) -> None:
        if self.config.enable_logger:
            logger.error(msg)

    def open_url(self, url: str | None) -> None:
        webbrowser.open(url or self.config.endpoint)

    def button_press(self, x: int, y: int, button: int) -> None:
        if button == 1:  # Left-click to open Kibana
            if self.config.kibana_url:
                self.open_url(self.config.kibana_url)
            else:
                self.open_url(self.config.endpoint)

    def safe_status_poll(self) -> str:
        try:
            # Only update if we're ready to draw
            if not self.layout or not self.drawer:
                return ""
            return self.get_elasticsearch_status()
        except Exception as e:
            self.log_errors(f"Failed during safe_status_poll: {e}")
            return self.format.format(
                symbol=self.config.error_symbol,
                label=self.config.get_label("ES"),
            )

    def get_elasticsearch_status(self) -> str:
        try:
            kwargs = {
                "hosts": [self.config.endpoint],
                "basic_auth": (self.config.username, self.config.password),
                "request_timeout": self.config.timeout,
                "verify_certs": self.config.verify_certs,
            }
            if self.config.ssl_ca:
                kwargs["ca_certs"] = self.config.ssl_ca
            es_client = ES(**kwargs)

            cluster_info = es_client.cluster.stats()
            cluster_name = cluster_info.get("cluster_name", "ES")

            health_data = es_client.cluster.health()
            status = health_data.get("status", "unknown")

            status_symbols = {
                "green": self.config.green_health_symbol,
                "yellow": self.config.yellow_health_symbol,
                "red": self.config.red_health_symbol,
                "unknown": self.config.unknown_health_symbol,
            }

            label = self.config.get_label(cluster_name)
            symbol = status_symbols.get(status, self.config.error_symbol)

            return self.format.format(symbol=symbol, label=label)
        except Exception as e:
            self.log_errors(str(e))
            return self.format.format(
                symbol=self.config.error_symbol,
                label=self.config.get_label("ES"),
            )
