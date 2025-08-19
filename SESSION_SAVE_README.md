# Session Save/Resume Functionality

## IRB-Approved Research - Safe Addition

This document describes the **non-intrusive save/resume functionality** added to the facial trust study program.

## 🛡️ IRB Compliance

- **No existing functionality modified** - all original routes and logic preserved
- **Non-intrusive additions only** - session management added as optional features
- **Graceful degradation** - if session manager fails, study continues normally
- **Data integrity maintained** - all existing data collection methods unchanged

## 🚀 How It Works

### **Automatic Session Saving**
- **When:** After each participant response (every trial)
- **Where:** `data/sessions/{participant_id}_session.json`
- **What:** Progress index, responses, face order, timestamps
- **Safety:** If save fails, study continues (non-critical)

### **Automatic Session Resume**
- **When:** Participant enters their ID on landing page
- **Check:** If incomplete session exists, offer resume
- **Restore:** All progress, responses, and face order
- **Safety:** If resume fails, starts new session (non-critical)

### **Session Completion**
- **When:** Participant completes the study
- **Action:** Mark session as complete
- **Prevents:** Accidental resume of completed sessions

## 📁 File Structure

```
facial-trust-study/
├── session_manager.py          # New: Session management functions
├── app.py                      # Modified: Added safe session calls
├── data/
│   ├── responses/              # Existing: Participant data
│   └── sessions/               # New: Session state files
│       └── {pid}_session.json  # Session data (JSON format)
```

## 🔧 Implementation Details

### **Session Manager Functions**
- `save_session_state()` - Save current progress
- `load_session_state()` - Load saved session
- `check_session_exists()` - Check for existing session
- `mark_session_complete()` - Mark session finished
- `get_session_progress()` - Calculate progress percentage

### **Integration Points**
1. **Task Route** - Save after each response
2. **Start Route** - Check for resume before creating new session
3. **Survey Route** - Mark session complete

### **Error Handling**
- All session operations wrapped in try/catch
- Failures logged but don't interrupt study
- Graceful fallback to original behavior

## 🧪 Testing

The session manager has been tested and verified to work correctly:
- ✅ Session saving
- ✅ Session loading
- ✅ Progress calculation
- ✅ Completion marking
- ✅ Error handling

## 📋 Usage

### **For Participants:**
1. **Start study** - Enter participant ID (1, 2, 3, 4 for testing)
2. **If interrupted** - Close browser, refresh, etc.
3. **Resume** - Enter same ID, automatically continues where left off
4. **Complete** - Session marked complete, can't resume

### **For Researchers:**
- **Session files** stored in `data/sessions/`
- **JSON format** for easy inspection
- **Timestamps** for audit trail
- **Progress tracking** for monitoring

## 🔒 Security & Privacy

- **Local storage only** - no external data transmission
- **Participant ID based** - no personal information stored
- **Session isolation** - each participant has separate file
- **No data loss** - existing CSV saving unchanged

## ⚠️ Important Notes

- **Backward compatible** - works with existing data
- **Optional feature** - study works without session manager
- **No IRB changes needed** - non-intrusive addition only
- **Test thoroughly** - verify with your specific setup

## 🎯 Benefits

1. **Data Protection** - No lost progress due to interruptions
2. **Participant Retention** - Easy resume reduces dropout
3. **Research Integrity** - Complete data collection
4. **IRB Compliance** - No protocol changes required
