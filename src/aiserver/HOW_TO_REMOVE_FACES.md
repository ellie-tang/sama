# How to Remove Faces from Known Faces List

## ✅ New Built-In Command (Recommended)

I've added a `/delete` command to both `app.py` and `app_ASI.py`.

### Usage

1. **Start the application:**
   ```bash
   cd LLM_Facial_Memory_System
   python app.py
   ```

2. **Use the `/delete` command:**
   ```
   You: /delete
   ```

3. **Select the face to delete:**
   ```
   Known faces:
   1. John (abc12345...)
   2. Jane (def67890...)
   3. Alice (ghi13579...)
   
   Enter number to delete (0 to cancel): 2
   ```

4. **Confirm deletion:**
   ```
   Delete 'Jane'? (yes/no): yes
   ✓ Deleted: Jane
   ```

### What Gets Deleted

The `/delete` command removes the face from:
- ✅ `face_embeddings.pkl` - Face recognition data
- ✅ `face_summaries.csv` - Summary about the person  
- ✅ Active faces - Currently detected faces
- ✅ Face memories - Conversation history in memory
- ✅ Message counts - Message count statistics

**Note:** Conversation history in `conversations.csv` is preserved for record-keeping.

---

## 🔧 Alternative: Manual Deletion (Without Running App)

If you want to delete a face without running the app, use the helper script I created:

### Step 1: Copy the Helper Script

```bash
cp /tmp/remove_face.py LLM_Facial_Memory_System/
cd LLM_Facial_Memory_System
```

### Step 2: Run the Script

**By face ID:**
```bash
python3 remove_face.py abc12345
```

**By name:**
```bash
python3 remove_face.py "John Doe"
```

### Output:
```
✓ Removed from face_embeddings.pkl: John Doe (abc12345)
✓ Removed from face_summaries.csv

✓ Successfully removed: John Doe
```

---

## 📋 Available Commands

When running the app, you now have these commands:

| Command | Description |
|---------|-------------|
| `/quit` | Exit the application |
| `/rename` | Rename a detected face |
| `/delete` | **Delete a face from the system** |
| `/faces` | Show all known faces |
| `/summary` | Show summaries for active faces |
| `/fix` | Fix CSV encoding issues |

---

## 🎯 Complete Example

```bash
# Start the app
cd LLM_Facial_Memory_System
python app.py

# See who's in the system
You: /faces

Known faces:
- John (abc12345...)
- Jane (def67890...)
- Unknown Person (ghi13579...)

# Delete the unknown person
You: /delete

Known faces:
1. John (abc12345...)
2. Jane (def67890...)
3. Unknown Person (ghi13579...)

Enter number to delete (0 to cancel): 3
Delete 'Unknown Person'? (yes/no): yes
✓ Deleted: Unknown Person

# Verify it's gone
You: /faces

Known faces:
- John (abc12345...)
- Jane (def67890...)

# Continue using the app or quit
You: /quit
```

---

## 🗑️ What Happens to Conversation History?

The `/delete` command **does NOT delete** conversation history from `conversations.csv`. This is intentional for record-keeping purposes.

If you want to also remove conversation history:

```bash
# Backup first!
cp conversations.csv conversations.csv.backup

# Edit conversations.csv manually or use this command:
# (Replace FACE_ID with the actual face ID)
grep -v "FACE_ID" conversations.csv > conversations.csv.tmp
mv conversations.csv.tmp conversations.csv
```

---

## 💡 Tips

1. **Use `/faces` first** to see all known faces before deleting
2. **Confirmation required** - The system will ask you to confirm deletion
3. **Cannot undo** - Once deleted, the face data is permanently removed
4. **Active faces** - If a face is currently active, it will be removed from active faces when deleted
5. **Re-training** - If you delete someone and want them back, you'll need to retrain or let the system detect them as a new person

---

## 🐛 Troubleshooting

**Problem:** "Face not found"  
**Solution:** Use `/faces` to see the exact face ID or name

**Problem:** Can't delete face  
**Solution:** Check file permissions on `face_embeddings.pkl` and `face_summaries.csv`

**Problem:** Face reappears after deletion  
**Solution:** Make sure you're not re-training the same person from `training_faces/` folder

---

## 📝 Summary

**Easiest method:** Use `/delete` command inside the running app

**Alternative:** Use the `remove_face.py` script when app is not running

**Both methods safely remove faces from all system components!**
