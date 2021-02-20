import logging

import requests

from rich_traceroute.config import get_recaptcha_settings

LOGGER = logging.getLogger(__name__)


class ReCaptcha:

    RECAPTCHA_ACTION = "submit_main_form"

    URL = "https://www.google.com/recaptcha/api.js"

    @staticmethod
    def is_used():
        return get_recaptcha_settings() is not None

    def __init__(self, ver: int):
        assert ver in (2, 3)

        self.ver = ver

        settings = get_recaptcha_settings()

        self.pub_key = settings[f"v{self.ver}"]["pub_key"]
        self.pvt_key = settings[f"v{self.ver}"]["pvt_key"]

    def check_user_response(self, user_recaptcha_data):
        url = "https://www.google.com/recaptcha/api/siteverify?"
        url = url + "secret=" + str(self.pvt_key)
        url = url + "&response=" + str(user_recaptcha_data)

        try:
            response = requests.get(url)
        except:  # noqa: E722
            LOGGER.exception(
                "Unhandled exception while performing recaptcha validation"
            )
            return True

        try:
            response.raise_for_status()
            data = response.json()
        except:  # noqa: E722
            LOGGER.exception(
                "Unhandled exception while processing recaptcha response: "
                f"{response}"
            )
            return True

        if (
            data["success"] and
            data.get("action", self.RECAPTCHA_ACTION) == self.RECAPTCHA_ACTION
        ):
            return True
        else:
            return False
