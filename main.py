from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api import router
from app.core import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

@app.get("/", include_in_schema=False)
def root():
    """ redirect main page """
    return RedirectResponse(url="/docs")

app.include_router(router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)