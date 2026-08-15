"""
Entry Point
Creates the FastAPI app and registers each layer's routes.
Run with: uvicorn app.main:app --reload

HOW THE PIECES FIT TOGETHER (a request travels down this stack):
    HTTP request
      -> CORS middleware        (is this browser origin allowed at all?)
      -> controller             (routing, status codes, RBAC gates)
      -> service                (the actual banking rules)
      -> app/data/database.py   (SQL against Neon/PostgreSQL)

WHY THE LAYERS ARE SPLIT THAT WAY: each one has exactly one reason to change.
Swapping the database touches only the bottom layer; changing who is allowed to
call something touches only the controller. If routing and money rules lived in
the same function, neither could be changed safely on its own.
"""

from fastapi import FastAPI
from app.controllers import customer_controller, account_controller, branch_controller
from app.controllers import auth_controller   # add this with your other controller imports
from app.controllers import analytics_controller
from fastapi.middleware.cors import CORSMiddleware
#need for for endpoints

app = FastAPI(title="SRTRS Bank API", version="1.0.0") #creates application object and sets title and version development

#connects each controller to the application so that the endpoints are available.
# Each controller carries its own URL prefix (e.g. /api/v1/customers), so the
# order of these lines does not matter -- there is no overlap to resolve.
app.include_router(customer_controller.router)
app.include_router(account_controller.router)
app.include_router(branch_controller.router)
app.include_router(auth_controller.router)     # add this with your other include_router lines
app.include_router(analytics_controller.router)


@app.get("/")
def root():
    # Unauthenticated health check. Useful for confirming the server is up
    # without needing a token -- the frontend and any monitoring can poll it.
    return {"message": "SRTRS Bank API is running"}


# CORS: browsers refuse cross-origin requests unless the server opts in, and the
# React dev server (localhost:5173) is a DIFFERENT origin from this API
# (127.0.0.1:8000). Without this block every fetch from the frontend fails in
# the browser -- even though the same request works fine from Postman or curl,
# because only browsers enforce the rule.
#
# allow_origins is an explicit allow-list rather than "*" on purpose: with
# allow_credentials=True the wildcard is rejected by the browser anyway, and
# naming the origin means a random website cannot drive this API using a
# logged-in user's session.
#
# NOTE: if you ever serve the frontend from a different port or deploy it, its
# URL has to be added here or the requests will start failing with a CORS error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)
