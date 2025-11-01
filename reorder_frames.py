import sys, os, shutil
from PIL import Image
import numpy as np

def compute_luma_hist(path):
    img = Image.open(path).convert('RGB')
    arr = np.asarray(img, dtype=np.uint8)
   
    r,g,b = arr[:,:,0].astype(np.float32), arr[:,:,1].astype(np.float32), arr[:,:,2].astype(np.float32)
    y = (0.299*r + 0.587*g + 0.114*b).astype(np.uint8).ravel()
    hist, _ = np.histogram(y, bins=256, range=(0,256))
    hist = hist.astype(np.float32)
    if hist.sum() > 0:
        hist /= hist.sum()
    return hist

def main():
    if len(sys.argv) < 4:
        print("Usage: python reorder_frames.py <frames_dir> <num_frames> <out_list.txt>")
        return
    frames_dir = sys.argv[1]
    N = int(sys.argv[2])
    out_list = sys.argv[3]

   
    files = sorted([f for f in os.listdir(frames_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))])
    if len(files) < N:
        print(f"Warning: found {len(files)} image files but expected {N}. Using found count.")
        N = len(files)
    files = files[:N]

    print(f"Using {N} frames from {frames_dir}")

    
    hists = []
    for i,f in enumerate(files):
        p = os.path.join(frames_dir, f)
        try:
            hist = compute_luma_hist(p)
        except Exception as e:
            print("Failed to open", p, "->", e)
            return
        hists.append(hist)
        if (i+1) % 50 == 0 or i == N-1:
            print(f"Computed hist for {i+1}/{N}")

    hists = np.stack(hists, axis=0)  

   
    print("Computing distance matrix...")
  
    aa = np.sum(hists*hists, axis=1, keepdims=True) 
    dist2 = aa + aa.T - 2.0 * (hists @ hists.T)
    np.fill_diagonal(dist2, np.inf)

    sums = dist2.sum(axis=1)
    cur = int(np.argmin(sums))
    print("Starting index:", cur, "file:", files[cur])

    used = np.zeros(N, dtype=bool)
    order = []
    for k in range(N):
        order.append(cur)
        used[cur] = True
      
        dist_row = dist2[cur].copy()
        dist_row[used] = np.inf
        if np.all(np.isinf(dist_row)):
        
            break
        cur = int(np.argmin(dist_row))
        if (k+1) % 50 == 0 or k == N-1:
            print(f"Ordered {k+1}/{N}")

    if len(order) < N:
        for i in range(N):
            if not used[i]:
                order.append(i)


    out_dir = os.path.join(os.getcwd(), "reordered")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    print("Writing reordered frames...")
 
    for new_idx, src_idx in enumerate(order):
        src_name = files[src_idx]
        src_path = os.path.join(frames_dir, src_name)
        ext = os.path.splitext(src_name)[1].lower()
        out_name = f"frame{new_idx:03d}{ext}"
        out_path = os.path.join(out_dir, out_name)
        shutil.copyfile(src_path, out_path)
        if (new_idx+1) % 50 == 0 or new_idx == N-1:
            print(f"Wrote {new_idx+1}/{N}")

    example_ext = os.path.splitext(files[0])[1].lower()
    with open(out_list, 'w', encoding='utf-8') as f:
        for i in range(N):
            name = f"frame{i:03d}{example_ext}"
            f.write(f"file 'reordered/{name}'\n")

    print("Done. Reordered frames in 'reordered/' and list file:", out_list)

if __name__ == "__main__":
    main()
