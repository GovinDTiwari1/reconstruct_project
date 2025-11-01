🎥 Jumbled Video Frame Reconstruction Project
🧩 Project Overview

This project reconstructs a jumbled or scrambled video by analyzing individual frames, determining the correct order, and rebuilding the video in its original sequence.

⚙️ 1. Installation Instructions
🧰 Requirements

Install these before running the project:

Tools

FFmpeg – for splitting and merging videos
👉 Download: https://www.gyan.dev/ffmpeg/builds/

Add the bin folder to your System PATH.
Test:

ffmpeg -version


GCC (MinGW) – for compiling the C reconstruction program
👉 Download: https://sourceforge.net/projects/mingw/

Test:

gcc --version


Python 3.10+ – for post-processing and optional reordering fix
Install dependencies:

pip install pillow numpy opencv-python

▶️ 2. How to Run the Code
Step 1 – Extract Frames

Extract frames from the input jumbled video:

ffmpeg -i jumbled_video.mp4 -start_number 0 -q:v 2 frames/frame%03d.jpg


✅ This saves all frames inside the frames/ folder as frame000.jpg, frame001.jpg, etc.

Step 2 – Compile the Reconstruction Code

Make sure reconstruct.c and stb_image.h are in the same folder.
Then compile:

gcc -O2 -lm -o reconstruct reconstruct.c

Step 3 – Generate the Frame Order

Run:

.\reconstruct frames 300 list.txt


👉 This will analyze the 300 frames and generate list.txt containing the reordered frame list.

Step 4 – Fix Frame Order(auto_reorder.py)

RUN auto_reorder.py

If the video looks reversed, run this Python script (reverse_list.py):

RUN reverse_list.py


Run:

python reverse_list.py

Step 5 – Rebuild the Video

Combine the ordered frames into a new video:

ffmpeg -f concat -safe 0 -i list_correct.txt -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -pix_fmt yuv420p final_fixed.mp4


✅ Output:

frames/ → Extracted frames

list.txt → Raw frame order

list_correct.txt → Fixed order

final_fixed.mp4 → Final reconstructed video

🧠 Algorithm Explanation
🔹 Technique Used

Similarity-Based Frame Sequencing

Each frame is compared with others using pixel difference and structural similarity (SSIM).

The frame with the highest similarity to the current one is chosen as the next frame.

🔹 Approach

Convert each frame to grayscale.

Measure similarity between frames using MSE or SSIM.

Starting from a random frame, iteratively find the most similar next frame.

Write the discovered order into list.txt.

If the video seems reversed, apply a mid-reverse heuristic.

🔹 Why This Method

✅ Simple and effective for smooth-motion videos

⚡ Avoids heavy AI/ML models (e.g., CNNs)

💻 Fast and efficient in C

| Factor          | Details                                              |
| --------------- | ---------------------------------------------------- |
| **Accuracy**    | Pixel-level comparison ensures fine-grained matching |
| **Complexity**  | O(n²) — acceptable for ≤ 500 frames                  |
| **Performance** | Can be parallelized for multi-core CPUs              |


⏱️ 4. Execution Time Log
| Step                        | Description                                  | Time Taken      |
| --------------------------- | -------------------------------------------- | --------------- |
| Frame Extraction            | Using FFmpeg (`jumbled_video.mp4 → frames/`) | ~2 seconds      |
| Frame Analysis & Reordering | C code (`reconstruct.c`)                     | ~6 seconds      |
| Final Video Reconstruction  | FFmpeg combine                               | ~2 seconds      |
| **Total**                   |                                              | **~10 seconds** |
