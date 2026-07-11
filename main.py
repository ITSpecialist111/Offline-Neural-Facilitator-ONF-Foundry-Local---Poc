"""Direct backend entry point.

For the complete application use ``.\\scripts\\start.ps1``. This file exists so
``py -3.12 main.py`` remains a valid, predictable command.
"""

import uvicorn


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000)
