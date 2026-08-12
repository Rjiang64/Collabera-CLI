"""
Entry Point
Creates the FastAPI app and registers each layer's routes.
Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from app.controllers import customer_controller, account_controller, branch_controller
from app.controllers import auth_controller   # add this with your other controller imports
from app.controllers import analytics_controller

#need for for endpoints 

app = FastAPI(title="Bank Management System API", version="1.0.0") #creates application object and sets title and version development

#connects each controller to the application so that the endpoints are available
app.include_router(customer_controller.router)  
app.include_router(account_controller.router)
app.include_router(branch_controller.router)
app.include_router(auth_controller.router)     # add this with your other include_router lines
app.include_router(analytics_controller.router)


@app.get("/")
def root():
    return {"message": "Bank Management System API is running"}
