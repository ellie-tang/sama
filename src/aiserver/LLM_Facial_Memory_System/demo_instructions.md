# Updated Face Recognition System

## Changes Made

The system has been modified to work with directory monitoring instead of webcam input:

### Key Changes:
1. **Removed webcam functionality** - No more camera capture or display windows
2. **Added directory monitoring** - System now monitors the `inputFaces` directory
3. **Automatic image processing** - New images are processed immediately when added
4. **Image preservation** - Images are kept after processing for your records

### New Workflow:
1. Run the application: `python app.py`
2. The system creates an `inputFaces` directory if it doesn't exist
3. Place image files (.jpg, .jpeg, .png, .bmp, .tiff, .webp) in the `inputFaces` directory
4. The system automatically:
   - Detects the new image
   - Performs face recognition
   - Updates active faces
   - Preserves the processed image (no deletion)
   - Prints recognition results to console

### Directory Structure:
- `inputFaces/` - Place new images here for processing
- `known_faces/` - Stores face embedding data
- `training_faces/` - For training new faces (organized by person folders)

### Dependencies Added:
- `watchdog` - For directory monitoring

### Installation:
```bash
pip install -r requirements.txt
```

### Usage Example:
1. Start the application: `python app.py`
2. Copy an image to `inputFaces/test.jpg`
3. System will automatically process and preserve the image
4. Continue chatting as normal - the system remembers who was in the last processed image

### Commands remain the same:
- `/quit` - Exit application
- `/rename` - Rename detected faces
- `/faces` - Show all known faces
- `/summary` - Show face summaries
- `/fix` - Fix CSV encoding issues