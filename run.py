import uvicorn

from app.config import AppRunConfig


if __name__ == "__main__":
    app_run_config = AppRunConfig.from_json()
    uvicorn.run("main:app", **app_run_config.dict())
