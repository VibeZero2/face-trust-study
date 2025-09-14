# **CRITICAL HANDOFF: Facial Trust Study Deployment Issue**

## **Problem Summary**
- **Local**: Works perfectly (35 faces, functional dashboard)
- **Render**: Shows 70 faces instead of 35, dashboard completely broken
- **Status**: Multiple fix attempts failed, needs fresh approach

## **Repository & Access**
- **GitHub**: https://github.com/VibeZero2/face-trust-study.git
- **Render App**: https://face-trust-study.onrender.com
- **Dashboard**: https://face-trust-study.onrender.com/dashboard
- **Local Workspace**: `C:\Users\Chris\CascadeProjects\facial-trust-study`
- **Local URL**: http://localhost:3000
- **Local Dashboard**: http://localhost:3000/dashboard

## **Current Local Setup**
- **Working Directory**: `C:\Users\Chris\CascadeProjects\facial-trust-study`
- **Main App Port**: 3000
- **Local URLs**:
  - Study: http://localhost:3000
  - Dashboard: http://localhost:3000/dashboard
- **Status**: Local deployment confirmed working correctly

## **Key Files to Examine**
- `app.py` - Main Flask app with face loading logic
- `wsgi_unified.py` - Render deployment entry point
- `dashboard/dashboard_app.py` - Dashboard blueprint
- `templates/task.html` - Shows "Face X of Y" display
- `static/images/` - Contains 35 face images

## **Critical Debugging Points**
1. **Face Loading**: `FACE_FILES` variable in `app.py` lines 54-64
2. **Session Creation**: `create_participant_run()` function - debug logs never appear on Render
3. **Sequence Display**: `task()` route shows wrong count in template
4. **Dashboard**: Blueprint registration and static file serving

## **What's Been Tried (Failed)**
- Session directory fixes
- Secret key unification
- WSGI architecture changes
- Extensive debug logging (logs never appear)

## **Immediate Actions Needed**
1. Compare exact runtime behavior: local vs Render
2. Trace why session creation debug logs don't appear on Render
3. Check if face files are being loaded twice or from wrong location
4. Verify dashboard blueprint routing and static files

## **Environment Setup**
```bash
cd C:\Users\Chris\CascadeProjects\facial-trust-study
pip install -r requirements.txt
python app.py  # Local testing on port 3000
```

## **Critical Issue**
The issue is urgent and the previous AI (Cascade) was unable to identify the root cause after multiple attempts. User needs this working ASAP.

## **CURRENT PROBLEM: Dashboard Delete Buttons Don't Work**

### STATUS:
- ✅ Local Flask app running on port 3000
- ✅ Dashboard accessible at http://localhost:3000/dashboard
- ✅ Delete buttons ARE visible on dashboard
- ❌ Delete buttons do NOT work - no server logs when clicked

### WHAT CASCADE TRIED:
1. **Login Issue**: Temporarily disabled @login_required decorator on delete_file function
2. **Redirect Bug**: Fixed url_for('dashboard') to url_for('dashboard.dashboard') 
3. **File Visibility**: Fixed production mode to show production files (not hide all files)
4. **Debug Logging**: Added extensive debug logging to delete_file function with 🗑️ emojis
5. **Form Debugging**: Added console.log to button onclick and form onsubmit

### THE CORE PROBLEM:
Delete buttons exist and are clickable, but clicking them produces:
- No Flask server logs (🗑️ DELETE FUNCTION CALLED never appears)
- No network requests visible
- No errors in browser console
- Form submission appears to fail silently

### KEY FILES MODIFIED:
- `/dashboard/dashboard_app.py` - delete_file function (line ~1874)
- `/dashboard/templates/dashboard.html` - delete button forms (line ~468)

### CURRENT DELETE FUNCTION:
```python
@dashboard_bp.route('/delete-file/<filename>', methods=['POST'])
# @login_required  # Temporarily disabled for local testing
def delete_file(filename):
    print(f"🗑️ DELETE FUNCTION CALLED: filename={filename}")
    # ... extensive debug logging throughout
```

### CURRENT FORM HTML:
```html
<form action="/dashboard/delete-file/{{ file.name }}" method="post" style="display: inline;" onsubmit="console.log('Form submitted for: {{ file.name }}');">
    <button type="submit" class="btn btn-danger btn-sm" onclick="console.log('Delete button clicked for: {{ file.name }}'); return confirm('Are you sure you want to delete this file?')">
        <i class="fas fa-trash"></i>
    </button>
</form>
```

### DEBUGGING STEPS FOR CURSOR:
1. Check browser dev tools console for JavaScript logs when delete clicked
2. Check browser Network tab for HTTP requests when delete clicked  
3. Verify form action URL is correct: `/dashboard/delete-file/filename.csv`
4. Test if route is accessible directly via browser/Postman
5. Check if there are any JavaScript errors preventing form submission

### SUSPECTED ISSUES:
- Form action URL might be malformed (spaces in filenames?)
- JavaScript confirm() dialog might be preventing submission
- Route registration issue with Flask blueprint
- CSRF token missing (though not implemented)

### ENVIRONMENT:
- Windows local development
- Flask app running on http://127.0.0.1:3000
- Dashboard at /dashboard/ route
- Files like "200.csv", "test123.csv" in data/responses/

### GOAL:
Get delete buttons to actually call the delete_file function and delete CSV files from data/responses directory.

### FILES TO CHECK:
- `dashboard/dashboard_app.py` (delete_file route)
- `dashboard/templates/dashboard.html` (form HTML)
- `app.py` (blueprint registration)

### PREVIOUS RENDER DEPLOYMENT ISSUES (RESOLVED):
- Face count issue: Fixed (shows 35 faces correctly)
- Dashboard broken: Fixed (fully functional)
- Data files missing: Fixed (test data deployed)
