from pathlib import Path
import re
path = Path("app.py")
text = path.read_text(encoding="utf-8")
pattern = re.compile(r"@app.route\(\"/\"\)\ndef landing\(\):.*?@app.route\(\"/instructions\"\)", re.S)
replacement = '''@app.route("/")
def landing():
    # Force consent first
    if "consent" not in session:
        return redirect(url_for("consent"))

    pid = request.args.get("pid")
    prolific_pid = request.args.get("PROLIFIC_PID", "")

    print(f"     LANDING DEBUG: PID from URL: {pid}")
    print(f"     LANDING DEBUG: Prolific PID from URL: {prolific_pid}")

    try:
        if pid:
            # Start session immediately
            print(f"     LANDING DEBUG: Creating session for PID: {pid}")
            create_participant_run(pid, prolific_pid)
            return redirect(url_for("task", pid=pid))

        # Pass prolific_pid to template if available
        return render_template("index.html", prolific_pid=prolific_pid)
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as log_file:
            log_file.write("[landing] " + str(e) + "\n")
            traceback.print_exc(file=log_file)
        raise

@app.route("/instructions")
def instructions():'''
new_text, count = pattern.subn(replacement, text)
if count == 0:
    raise SystemExit('landing block not found')
path.write_text(new_text, encoding="utf-8")
