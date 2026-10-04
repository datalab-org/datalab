# This file was edited with the assistance of an AI model and requires human review from the contributor.
# The server-side implementation still lives in core datalab for now; this
# re-export gives the plugin an entry point so its webapp component is collected.
from pydatalab.apps.chat import ChatBlock

__all__ = ("ChatBlock",)
