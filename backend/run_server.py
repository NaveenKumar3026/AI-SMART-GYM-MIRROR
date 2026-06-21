import uvicorn

if __name__ == "__main__":
    # Programmatic runner avoids shell quoting issues on Windows PowerShell
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
