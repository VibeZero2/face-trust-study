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
