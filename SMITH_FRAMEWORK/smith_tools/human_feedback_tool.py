"""
SMITH Human Feedback Tool
-------------------------

Этот модуль предоставляет интерфейс для запросов подтверждения или
уточнения у человека‑оператора.  В будущем он может быть расширен
интерактивными UI, интеграцией с чат‑клиентами или веб‑интерфейсом.

В текущей минимальной реализации запрос просто выводится в stdout, и
возвращается True, имитируя согласие пользователя.  Это позволяет
обходить блокирующий ввод при запуске автоматических тестов.  При
необходимости поведения по умолчанию можно контролировать через
переменную окружения ``SMITH_AUTO_CONFIRM``: если она установлена в
``"false"`` (без кавычек), метод `request_confirmation` будет
возвращать False.
"""

import os
from typing import Optional


class HumanFeedbackTool:
    """A tool for requesting confirmation or clarification from the user.

    The tool operates in two modes:

    * **Auto‑confirm mode** (default when ``SMITH_AUTO_CONFIRM`` is set):
      confirmations are automatically accepted or declined based on the
      environment variable.  This is useful for automated testing or batch
      processing where user interaction is undesirable.

    * **Interactive mode** (default when no ``SMITH_AUTO_CONFIRM`` is set):
      the tool prompts the user on the command line and waits for a "yes"
      or "no" style response.  A blank response counts as "yes".  Any
      response beginning with ``y`` (case‑insensitive) is treated as a
      confirmation, otherwise the action is declined.  If input cannot be
      read (e.g. in a non‑interactive environment), the confirmation
      defaults to ``False``.

    Parameters
    ----------
    auto_confirm : Optional[bool], optional
        Override the auto‑confirm behaviour programmatically.  If
        ``None`` (default), the value of the ``SMITH_AUTO_CONFIRM``
        environment variable is consulted.  If the environment variable
        is unset, interactive mode is enabled.
    """

    def __init__(self, auto_confirm: Optional[bool] = None) -> None:
        env_value = os.getenv("SMITH_AUTO_CONFIRM")
        if env_value is not None:
            # Environment variable explicitly sets confirmation; any value
            # other than the string "false" (case‑insensitive) is treated
            # as True.  This disables interactive prompts.
            self.auto_confirm = env_value.lower() != "false"
            self.interactive = False
        else:
            # If auto_confirm parameter was provided explicitly, use it;
            # otherwise defer to interactive mode (None means ask).
            self.auto_confirm = auto_confirm
            self.interactive = auto_confirm is None

    def request_confirmation(self, prompt: str) -> bool:
        """
        Ask the user to confirm or decline a potentially dangerous action.

        In interactive mode, the user is presented with the question and
        asked to respond with yes/no.  In auto‑confirm mode, the stored
        setting determines the response.

        Parameters
        ----------
        prompt : str
            The message describing the operation requiring confirmation.

        Returns
        -------
        bool
            ``True`` if the operation is confirmed, ``False`` otherwise.
        """
        # Always display the prompt to give context to the user or logs.
        print(f"[HUMAN FEEDBACK REQUIRED] {prompt}")
        # Auto‑confirm mode: return preconfigured value (default True)
        if not self.interactive:
            # If self.auto_confirm is None, default to True
            return bool(self.auto_confirm) if self.auto_confirm is not None else True
        # Interactive mode: ask the user
        try:
            # Provide a simple yes/no prompt.  Accept empty input as "yes".
            response = input(f"{prompt} [y/N]: ").strip().lower()
            if not response:
                return True  # default to yes on empty input
            return response[0] == "y"
        except Exception:
            # In non‑interactive environments (no stdin), decline by default
            return False