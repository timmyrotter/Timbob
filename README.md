# Continuous Integration Exercise

This is an exercise containing some basics tests to practice setting up continuous integration for automated testing.  See the assignment description for more details!

## Running the Choose My College demo

The `app.py` module in the repository root boots the Choose My College (CMC) demo that was
used throughout the exercises. It is completely self-contained and only relies on the Python
standard library.

1. **Install Python 3.10 or newer.** No virtual environment is required, though you can use one
   if you prefer.
2. **Start the server:**

   ```bash
   python app.py
   ```

   The console prints the address (defaults to <http://127.0.0.1:5000>) and the running
   version so you can confirm you are on the latest build.
3. **Visit the site:** Open the printed address in your browser. If you ran an older version
   before, force-refresh the page (Ctrl/Cmd + Shift + R) so the new stylesheet is fetched.

### Helpful command-line options

The server accepts a handful of optional flags:

```bash
python app.py --host 127.0.0.1 --port 8000      # choose a different interface/port
python app.py --reset                           # delete the existing cmc.db before launch
```

Use `--reset` if you want to reseed the database (for example, to get the new campus imagery that
ships with the refreshed UI). The command reports when it removes an existing database file so you
know the fresh seed will be applied on startup.
