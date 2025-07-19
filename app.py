import os
import csv
import random
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, abort
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# ----------------------------------------------------------------------------
# Initial setup
# ----------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# Encryption key (must be 32 url-safe base64-encoded bytes)
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY missing in .env")
fernet = Fernet(FERNET_KEY)

# Folder constants
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "static" / "images"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load image list once at startup.
# We accept any JPG/PNG in the folder and will present the SAME image three times
# (left crop, right crop, full) using CSS clipping.
# Accept .jpg or .jpeg in any capitalization
FACE_FILES = []
for pattern in ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG"):
    FACE_FILES.extend([p.name for p in IMAGES_DIR.glob(pattern)])
# Deduplicate by filename stem (without extension) to avoid counting duplicates
unique = {}
for fname in FACE_FILES:
    stem = Path(fname).stem
    if stem not in unique:
        unique[stem] = fname  # keep first occurrence
FACE_FILES = sorted(unique.values())
assert FACE_FILES, "No face images found. Place images in static/images/."

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------

def create_participant_run(pid: str):
    """Initialises session variables for a new participant."""
    # Randomly pick left-first or right-first presentation
    left_first = random.choice([True, False])
    
    # Randomize the order of face files for this participant
    # Use a copy to avoid modifying the original FACE_FILES list
    randomized_faces = FACE_FILES.copy()
    random.shuffle(randomized_faces)
    
    # Store the randomized order for analysis
    face_order = [Path(fname).stem for fname in randomized_faces]
    
    sequence = []
    for fname in randomized_faces:
        # order list simply contains the same filename with a tag indicating crop
        if left_first:
            halves = [
                {"version": "left", "file": fname},
                {"version": "right", "file": fname},
            ]
        else:
            halves = [
                {"version": "right", "file": fname},
                {"version": "left", "file": fname},
            ]
        sequence.append({
            "face_id": Path(fname).stem,
            "order": [{"version": "toggle", "file": fname, "start": ("left" if left_first else "right")}, {"version": "full", "file": fname}]
        })
    
    session["pid"] = pid
    session["index"] = 0  # index in sequence
    session["sequence"] = sequence
    session["responses"] = []
    session["face_order"] = face_order  # Store the randomized face order


def save_encrypted_csv(pid: str, rows: list):
    """Encrypts and saves participant data."""
    csv_content = csv.StringIO()
    writer = csv.writer(csv_content)
    # header
    writer.writerow([
        "pid", "timestamp", "face_id", "version", "order_presented",
        "trust_rating", "masc_choice", "fem_choice",
        "trust_q1", "trust_q2", "trust_q3",
        "pers_q1", "pers_q2", "pers_q3", "pers_q4", "pers_q5"
    ])
    writer.writerows(rows)
    
    # Save face order information in a separate row
    if "face_order" in session:
        face_order_row = [pid, datetime.utcnow().isoformat(), "face_order", "metadata", "", "", "", "", "", "", "", "", "", "", "", ""]
        writer.writerow(face_order_row)
        # Add the face order as additional rows with index numbers
        for i, face_id in enumerate(session["face_order"]):
            order_row = [pid, "", face_id, "order_index", i+1, "", "", "", "", "", "", "", "", "", "", ""]
            writer.writerow(order_row)
    
    # Save plaintext CSV (for immediate analysis)
    plain_path = DATA_DIR / f"{pid}.csv"
    plain_path.write_text(csv_content.getvalue(), encoding="utf-8")

    # Encrypt and save the same content
    token = fernet.encrypt(csv_content.getvalue().encode())
    outfile = DATA_DIR / f"{pid}.csv.enc"
    with outfile.open("wb") as f:
        f.write(token)

    # Also save a plaintext Excel copy for quick inspection
    try:
        import pandas as pd
        # Create main dataframe with responses
        df = pd.DataFrame(rows, columns=[
            "pid", "timestamp", "face_id", "version", "order_presented",
            "trust_rating", "masc_choice", "fem_choice",
            "trust_q1", "trust_q2", "trust_q3",
            "pers_q1", "pers_q2", "pers_q3", "pers_q4", "pers_q5"
        ])
        
        # Add face order information to a separate sheet
        if "face_order" in session:
            face_order_df = pd.DataFrame({
                "position": range(1, len(session["face_order"])+1),
                "face_id": session["face_order"]
            })
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(DATA_DIR / f"{pid}.xlsx") as writer:
                df.to_excel(writer, sheet_name="Responses", index=False)
                face_order_df.to_excel(writer, sheet_name="Face Order", index=False)
        else:
            df.to_excel(DATA_DIR / f"{pid}.xlsx", index=False)
    except ImportError:
        pass  # pandas not installed; Excel export skipped

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.route("/consent", methods=["GET", "POST"])
def consent():
    """Informed consent page shown before anything else."""
    if request.method == "POST":
        choice = request.form.get("choice")
        if choice == "agree":
            session["consent"] = True
            return redirect(url_for("landing"))
        # Declined – clear session and show goodbye
        session.clear()
        return render_template("declined.html")
    return render_template("consent.html")


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if "pid" not in session:
        return redirect(url_for("landing"))
    if request.method == "POST":
        t1 = request.form.get("trust1")
        t2 = request.form.get("trust2")
        t3 = request.form.get("trust3")
        p1 = request.form.get("pers1")
        p2 = request.form.get("pers2")
        p3 = request.form.get("pers3")
        p4 = request.form.get("pers4")
        p5 = request.form.get("pers5")
        session["responses"].append([
            session["pid"], datetime.utcnow().isoformat(), "survey", "survey", session["index"],
            None, None, None,
            t1, t2, t3, p1, p2, p3, p4, p5
        ])
        # Save and finish
        save_encrypted_csv(session["pid"], session["responses"])
        pid = session["pid"]
        session.clear()
        return redirect(url_for("done", pid=pid))
    return render_template("survey.html")


@app.route("/")
def landing():
    # Force consent first
    if "consent" not in session:
        return redirect(url_for("consent"))

    pid = request.args.get("pid")
    if pid:
        # Start session immediately
        create_participant_run(pid)
        return redirect(url_for("task", pid=pid))
    return render_template("index.html")

@app.route("/instructions")
def instructions():
    if "pid" not in session:
        return redirect(url_for("landing"))
    return render_template("instructions.html")


@app.route("/start", methods=["POST"])
def start_manual():
    pid = request.form.get("pid", "").strip()
    if not pid:
        abort(400)
    create_participant_run(pid)
    return redirect(url_for("instructions"))

@app.route("/task", methods=["GET", "POST"])
def task():
    # If session missing but pid present in query (e.g., redirect loop), rebuild session
    if "pid" not in session:
        qpid = request.args.get("pid")
        if qpid:
            create_participant_run(qpid)
        else:
            return redirect(url_for("landing"))

    # Handle POST (save previous answer)
    if request.method == "POST":
        data = session["sequence"][session["index"] // 3]
        face_id = data["face_id"]
        version = request.form["version"]
        if version == "toggle":
            trust_left = request.form.get("trust_left")
            trust_right = request.form.get("trust_right")
            # record left then right (order flag indicates which shown first but both stored)
            row_l = [
                session["pid"], datetime.utcnow().isoformat(), face_id,
                "left", session["index"], trust_left, None, None
            ]
            while len(row_l) < 16:
                row_l.append(None)
            session["responses"].append(row_l)
            row_r = [
                session["pid"], datetime.utcnow().isoformat(), face_id,
                "right", session["index"], trust_right, None, None
            ]
            while len(row_r) < 16:
                row_r.append(None)
            session["responses"].append(row_r)
        else:
            trust_rating = request.form.get("trust")
            masc_choice = request.form.get("masc")
            fem_choice = request.form.get("fem")
            row_o = [
                session["pid"], datetime.utcnow().isoformat(), face_id,
                version, session["index"], trust_rating, masc_choice, fem_choice
            ]
            while len(row_o) < 16:
                row_o.append(None)
            session["responses"].append(row_o)
        session["index"] += 1

    # Check if finished
    if session["index"] >= len(session["sequence"]) * 2:  # 2 stages per face (toggle and full)
        return redirect(url_for("survey"))

    # Determine current image to show
    face_index = session["index"] // 2
    image_index = session["index"] % 2
    current = session["sequence"][face_index]
    image_dict = current["order"][image_index]
    image_file = image_dict["file"]
    version = image_dict["version"]
    if version == "toggle":
        side = image_dict.get("start", "left")
    else:
        side = version

    # Determine which blocks to show in template
    show_mf_questions = version == "compare"
    show_trust_questions = version in ("toggle", "full")

    progress = face_index + 1
    return render_template(
        "task.html",
        pid=session["pid"],
        image_url=url_for("static", filename=f"images/{image_file}"),
        face_id=current["face_id"],
        version=version,
        progress=progress,
        total=len(FACE_FILES),
        show_mf=show_mf_questions,
        show_trust=show_trust_questions,
        side=side,
    )

@app.route("/done")
def done():
    pid = request.args.get("pid")
    return render_template("done.html", pid=pid)

# ----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
