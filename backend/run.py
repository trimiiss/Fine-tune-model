import uvicorn

if __name__ == "__main__":
    # Keep the launcher single-process so it is reliable on Windows and in
    # constrained local environments. Use `uvicorn app.main:app --reload` if
    # you specifically want hot reload during development.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
