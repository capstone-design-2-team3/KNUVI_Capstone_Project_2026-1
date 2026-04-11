# Made using Gemini cli (gemini 3.0 pro)

#!/bin/bash

# 3DGS Adverse Weather Dataset Preparation Script
# This script performs:
# 1. 3n-th frame deletion (Redundancy removal)
# 2. Evenly spaced subsampling (Limit total frames)
# 3. Reindexing (00001.png ~) and Mapping generation

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <directory_path> [max_frames (default: 200)]"
    exit 1
fi

TARGET_DIR=$1
MAX_FRAMES=${2:-200}

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR not found."
    exit 1
fi

DIR_NAME=$(basename "$TARGET_DIR")
MAP_FILE="${DIR_NAME}_mapping.txt"
TMP_DIR="${TARGET_DIR}_tmp_prep"

echo "--------------------------------------------------"
echo "Target Directory: $TARGET_DIR"
echo "Max Frames      : $MAX_FRAMES"
echo "--------------------------------------------------"

# Step 1: Initial redundancy removal (Delete every 3rd frame)
# Note: If already done, this step might be skipped or modified based on needs.
echo "[1/3] Removing every 3rd frame (3n-th)..."
ls -1 "$TARGET_DIR"/*.png | sort | awk 'NR % 3 == 0' | xargs rm 2>/dev/null

# Step 2: Subsampling to match MAX_FRAMES
TOTAL_COUNT=$(ls -1 "$TARGET_DIR"/*.png | wc -l | xargs)
echo "Current image count: $TOTAL_COUNT"

if [ "$TOTAL_COUNT" -gt "$MAX_FRAMES" ]; then
    echo "[2/3] Subsampling to $MAX_FRAMES frames (Evenly spaced)..."
    ls -1 "$TARGET_DIR"/*.png | sort | awk -v n="$TOTAL_COUNT" -v m="$MAX_FRAMES" '
        BEGIN {
            for (i=0; i<m; i++) {
                keep[int(i * (n-1) / (m-1)) + 1] = 1
            }
        }
        { if (!(NR in keep)) print $0 }
    ' | xargs rm
    echo "Reduced to $(ls -1 "$TARGET_DIR"/*.png | wc -l | xargs) images."
else
    echo "[2/3] Skipping subsampling (Already under $MAX_FRAMES)."
fi

# Step 3: Reindexing and Mapping
echo "[3/3] Reindexing images and creating mapping..."
mkdir -p "$TMP_DIR"
FINAL_FILES=($(ls -1 "$TARGET_DIR"/*.png | sort))
COUNT=1

# Clear mapping file if exists
> "$MAP_FILE"

for FILE in "${FINAL_FILES[@]}"; do
    NEW_NAME=$(printf "%05d.png" $COUNT)
    OLD_IDX=$(basename "$FILE" .png)
    
    # Copy to tmp with new name
    cp "$FILE" "$TMP_DIR/$NEW_NAME"
    
    # Record mapping [New : Old]
    echo "$(printf "%05d" $COUNT) : $OLD_IDX" >> "$MAP_FILE"
    
    ((COUNT++))
done

# Replace original files with reindexed ones
rm "$TARGET_DIR"/*.png
mv "$TMP_DIR"/*.png "$TARGET_DIR/"
rmdir "$TMP_DIR"

echo "--------------------------------------------------"
echo "Success! Final count: $((COUNT-1))"
echo "Mapping saved to: $MAP_FILE"
echo "--------------------------------------------------"
