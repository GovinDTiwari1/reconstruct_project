import sys, os, shutil
import numpy as np
from PIL import Image

def load_gray(path, resize=(128,128)):
    im = Image.open(path).convert('L')
    if resize is not None:
        im = im.resize(resize, Image.BILINEAR)
    return np.asarray(im, dtype=np.float32) / 255.0

def ssim_simple(a,b):
    C1 = 0.01**2
    C2 = 0.03**2
    mu1 = a.mean(); mu2 = b.mean()
    s1 = a.var(); s2 = b.var()
    s12 = ((a-mu1)*(b-mu2)).mean()
    den = (mu1*mu1 + mu2*mu2 + C1) * (s1 + s2 + C2)
    if den == 0:
        return 0.0
    return ((2*mu1*mu2 + C1) * (2*s12 + C2)) / den

def pairwise_similarity(imgs):
    N = len(imgs)
    S = np.zeros((N,N), dtype=np.float32)
    for i in range(N):
        for j in range(i+1, N):
            v = ssim_simple(imgs[i], imgs[j])
            S[i,j] = S[j,i] = v
    np.fill_diagonal(S, -1.0)
    return S

def greedy_nn(S):
    avg = S.sum(axis=1)
    cur = int(np.argmax(avg))
    N = S.shape[0]
    used = np.zeros(N, bool)
    order = []
    for _ in range(N):
        order.append(cur)
        used[cur] = True
        row = S[cur].copy()
        row[used] = -1.0
        if np.all(row <= -1.0):
            break
        cur = int(np.argmax(row))
    if len(order) < N:
        for i in range(N):
            if not used[i]:
                order.append(i)
    return order

def two_opt(order, S, iter_limit=200):
    N = len(order)
    best = order[:]
    improved = True
    it = 0
    while improved and it < iter_limit:
        improved = False
        it += 1
        for i in range(1, N-2):
            for j in range(i+1, N-1):
                a,b = best[i-1], best[i]
                c,d = best[j], best[j+1]
                old = S[a,b] + S[c,d]
                new = S[a,c] + S[b,d]
                if new > old + 1e-9:
                    best[i:j+1] = list(reversed(best[i:j+1]))
                    improved = True
    return best

def write_reordered(files, order, frames_dir, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    ext = os.path.splitext(files[0])[1].lower()
    for k, idx in enumerate(order):
        src = os.path.join(frames_dir, files[idx])
        dst = os.path.join(out_dir, f"frame{k:03d}{ext}")
        shutil.copyfile(src, dst)
    return ext

def write_list(out_list, out_dir, ext, N):
    with open(out_list, 'w', encoding='utf-8') as f:
        for i in range(N):
            f.write(f"file '{out_dir}/frame{i:03d}{ext}'\n")

def main():
    if len(sys.argv) < 4:
        print("Usage: python reorder_and_optimize.py <frames_dir> <num_frames> <out_list>")
        return
    frames_dir = sys.argv[1]
    N = int(sys.argv[2])
    out_list = sys.argv[3]
    files_all = sorted([f for f in os.listdir(frames_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))])
    if len(files_all) == 0:
        print("No frames found in", frames_dir); return
    if len(files_all) < N:
        N = len(files_all)
    files = files_all[:N]
    imgs = [load_gray(os.path.join(frames_dir, f), resize=(128,128)) for f in files]
    S = pairwise_similarity(imgs)
    order = greedy_nn(S)
    order_opt = two_opt(order, S, iter_limit=300)
    if sum(S[order_opt[i], order_opt[i+1]] for i in range(len(order_opt)-1)) >= sum(S[order[i], order[i+1]] for i in range(len(order)-1)):
        order = order_opt
    forward_score = sum(S[order[i], order[i+1]] for i in range(len(order)-1))
    reverse_score = sum(S[order[::-1][i], order[::-1][i+1]] for i in range(len(order)-1))
    if reverse_score > forward_score:
        order = order[::-1]
    out_dir = "reordered"
    ext = write_reordered(files, order, frames_dir, out_dir)
    write_list(out_list, out_dir, ext, N)
    print("Wrote reordered frames to", out_dir, "and list file", out_list)

if __name__ == "__main__":
    main()
