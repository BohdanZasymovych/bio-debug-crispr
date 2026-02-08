from prompts.diagnostician_prompt import DIAGNOSTICIAN_PROMPT
from prompts.engineer_prompt import ENGINEER_PROMPT

try:
    from prompts.regulator_prompt import REGULATOR_PROMPT
    __all__ = ["DIAGNOSTICIAN_PROMPT", "ENGINEER_PROMPT", "REGULATOR_PROMPT"]
except ImportError:
    __all__ = ["DIAGNOSTICIAN_PROMPT", "ENGINEER_PROMPT"]
