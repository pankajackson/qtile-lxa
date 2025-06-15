import webbrowser
from qtile_extras.widget import GenPollText
import requests
from urllib.parse import urlparse
from libqtile.log_utils import logger
from typing import Any
from .typing import URLMonitorConfig


class URLMonitor(GenPollText):
    def __init__(
        self,
        config: URLMonitorConfig,
        **kwargs: Any,
    ):
        self.config = config
        self.config.label = self.config.label or self.config.url
        self.format = "{symbol} {label}"
        super().__init__(func=self.check_url_status, **kwargs)

    def log_errors(self, msg):
        if self.config.enable_logger:
            logger.error(msg)

    def open_url(self):
        webbrowser.open(self.config.url)

    def button_press(self, x, y, button):
        if button == 1:  # Mouse button 1 (left click)
            self.open_url()

    def check_url_status(self):
        try:
            parsed_url = urlparse(self.config.url)
            if not parsed_url.scheme:
                self.config.url = f"{self.config.schema}://{self.config.url}"

            response = requests.get(
                self.config.url,
                timeout=self.config.timeout,
                verify=self.config.cert_verify,
            )
            if response.status_code == 200:
                status_symbol = self.config.success_symbol
            else:
                status_symbol = self.config.failure_symbol
            return self.format.format(symbol=status_symbol, label=self.config.label)
        except requests.RequestException as e:
            self.log_errors(str(e))
            return self.format.format(
                symbol=self.config.error_symbol,
                label=self.config.label,
            )
        except Exception as e:
            self.log_errors(str(e))
            return self.format.format(
                symbol=self.config.unknown_symbol,
                label=self.config.label,
            )
