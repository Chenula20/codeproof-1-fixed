import os
import secrets

import uvicorn

from .app import create_app


if __name__ == "__main__":
    if not os.environ.get("CODEPROOF_TOKEN"):
        os.environ["CODEPROOF_TOKEN"] = secrets.token_urlsafe(32)
        print("Paste this local pairing token into CodeProof's Connect project dialog:")
        print(os.environ["CODEPROOF_TOKEN"])
    print("CodeProof local service: http://127.0.0.1:8000")
    uvicorn.run(create_app(), host="127.0.0.1", port=8000, access_log=False)
