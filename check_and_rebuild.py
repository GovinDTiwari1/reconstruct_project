import os, subprocess, sys

def count_frames(exts=(".jpg",".png",".jpeg")):
    files = []
    for e in exts:
        files = sorted([f for f in os.listdir("frames") if f.lower().endswith(e)])
        if files:
            return files, e
    return [], None

files, ext = count_frames()
print("Found", len(files), "frames, extension:", ext)
if len(files) <= 1:
    print("-> Need to re-extract frames. Run:")
    print("ffmpeg -i reconstructed.mp4 -start_number 0 -q:v 2 frames/frame%03d"+ext)
    sys.exit(1)

# create list_fixed.txt (Windows-friendly)
with open("list_fixed.txt","w",encoding="utf-8") as f:
    for name in files:
        f.write(f"file 'frames/{name}'\n")
print("Wrote list_fixed.txt with", len(files), "entries")

# attempt concat method first (some Windows builds of ffmpeg accept it)
ret = subprocess.call([
    "ffmpeg","-y","-f","concat","-safe","0","-i","list_fixed.txt",
    "-vf","scale=trunc(iw/2)*2:trunc(ih/2)*2","-c:v","libx264","-pix_fmt","yuv420p","final_by_concat.mp4"
])
if ret == 0:
    print("Created final_by_concat.mp4")
else:
    print("Concat failed, building from image sequence...")
    # detect start number
    first = files[0]
    num = int(''.join(ch for ch in os.path.splitext(first)[0] if ch.isdigit()) or 0)
    start = 0 if num==0 else 1
    cmd = ["ffmpeg","-y","-framerate","30","-start_number",str(start),"-i",f"frames/frame%03d{ext}",
           "-c:v","libx264","-pix_fmt","yuv420p","final_by_sequence.mp4"]
    subprocess.call(cmd)
    print("Created final_by_sequence.mp4 (check the file).")
