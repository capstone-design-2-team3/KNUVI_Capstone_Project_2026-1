# Made using Gemini cli (gemini 3.0 pro)

#!/bin/bash

# 3DGS Adverse Weather Dataset Preparation Script
# This script performs:
# 1. Standard Mode: 3n-th frame deletion, Subsampling, and Reindexing
# 2. Sync Mode: Applying an existing mapping file to sync frames (e.g. original to rain/snow)

if [ "$#" -lt 1 ]; then
    echo "Usage (Standard): $0 <directory_path> [max_frames (default: 200)]"
    echo "Usage (Sync Mode): $0 <directory_path> <mapping_file>"
    exit 1
fi

TARGET_DIR=$1
ARG2=$2

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR not found."
    exit 1
fi

# Detect Mode
if [ -f "$ARG2" ]; then
    MODE="SYNC"
    MAP_FILE="$ARG2"
    echo "--------------------------------------------------"
    echo "Mode            : Sync (Applying mapping)"
    echo "Target Directory: $TARGET_DIR"
    echo "Mapping File    : $MAP_FILE"
    echo "--------------------------------------------------"
else
    MODE="PREP"
    MAX_FRAMES=${ARG2:-200}
    echo "--------------------------------------------------"
    echo "Mode            : Standard Preparation"
    echo "Target Directory: $TARGET_DIR"
    echo "Max Frames      : $MAX_FRAMES"
    echo "--------------------------------------------------"
fi

DIR_NAME=$(basename "$TARGET_DIR")
TMP_DIR="${TARGET_DIR}_tmp_prep"
INPUT_DIR="$TARGET_DIR/input"

if [ "$MODE" == "PREP" ]; then
    # Step 1: Initial redundancy removal (Delete every 3rd frame)
    echo "[1/3] Removing every 3rd frame (3n-th)..."
    ls -1 "$TARGET_DIR"/*.png 2>/dev/null | sort | awk 'NR % 3 == 0' | xargs rm 2>/dev/null

    # Step 2: Subsampling to match MAX_FRAMES
    TOTAL_COUNT=$(ls -1 "$TARGET_DIR"/*.png 2>/dev/null | wc -l | xargs)
    echo "Current image count: $TOTAL_COUNT"

    if [ "$TOTAL_COUNT" -gt "$MAX_FRAMES" ]; then
        echo "[2/3] Subsampling to $MAX_FRAMES frames (Evenly spaced)..."
        ls -1 "$TARGET_DIR"/*.png 2>/dev/null | sort | awk -v n="$TOTAL_COUNT" -v m="$MAX_FRAMES" '
            BEGIN {
                for (i=0; i<m; i++) {
                    keep[int(i * (n-1) / (m-1)) + 1] = 1
                }
            }
            { if (!(NR in keep)) print $0 }
        ' | xargs rm 2>/dev/null
        echo "Reduced to $(ls -1 "$TARGET_DIR"/*.png 2>/dev/null | wc -l | xargs) images."
    else
        echo "[2/3] Skipping subsampling (Already under $MAX_FRAMES)."
    fi

    # Step 3: Reindexing and Mapping
    echo "[3/3] Reindexing images and creating mapping..."
    mkdir -p "$TMP_DIR"
    FINAL_FILES=($(ls -1 "$TARGET_DIR"/*.png 2>/dev/null | sort))
    COUNT=1
    
    NEW_MAP_FILE="${DIR_NAME}_mapping.txt"
    > "$NEW_MAP_FILE"

    for FILE in "${FINAL_FILES[@]}"; do
        NEW_NAME=$(printf "%05d.png" $COUNT)
        OLD_IDX=$(basename "$FILE" .png)
        cp "$FILE" "$TMP_DIR/$NEW_NAME"
        echo "$(printf "%05d" $COUNT) : $OLD_IDX" >> "$NEW_MAP_FILE"
        ((COUNT++))
    done

    # Move to input/ subdirectory
    rm "$TARGET_DIR"/*.png 2>/dev/null
    mkdir -p "$INPUT_DIR"
    mv "$TMP_DIR"/*.png "$INPUT_DIR/"
    rmdir "$TMP_DIR"

    echo "--------------------------------------------------"
    echo "Success! Final count: $((COUNT-1))"
    echo "Mapping saved to: $NEW_MAP_FILE"
    echo "Images moved to : $INPUT_DIR"
    echo "--------------------------------------------------"

else
    # Sync Mode Logic
    echo "[1/1] Syncing frames using $MAP_FILE..."
    mkdir -p "$TMP_DIR"
    COUNT=0

    while IFS=':' read -r target source; do
        # Trim whitespace
        target=$(echo $target | xargs)
        source=$(echo $source | xargs)
        
        if [[ -z "$target" || -z "$source" ]]; then continue; fi
        
        SOURCE_FILE="$TARGET_DIR/$source.png"
        TARGET_FILE="$TMP_DIR/$target.png"
        
        if [ -f "$SOURCE_FILE" ]; then
            cp "$SOURCE_FILE" "$TARGET_FILE"
            ((COUNT++))
        else
            echo "Warning: Source $SOURCE_FILE not found."
        fi
    done < "$MAP_FILE"

    # Move to input/ subdirectory
    rm "$TARGET_DIR"/*.png 2>/dev/null
    mkdir -p "$INPUT_DIR"
    mv "$TMP_DIR"/*.png "$INPUT_DIR/"
    rmdir "$TMP_DIR"

    echo "--------------------------------------------------"
    echo "Success! Synced $COUNT frames."
    echo "Images moved to : $INPUT_DIR"
    echo "--------------------------------------------------"
fi

