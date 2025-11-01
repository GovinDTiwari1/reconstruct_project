import os, shutil, subprocess, sys
import numpy as np
from PIL import Image

def list_frames(dirname):
    names = sorted([f for f in os.listdir(dirname) if f.lower().endswith(('.jpg','.jpeg','.png'))])
    return names

def load_gray(path, resize=(128,128)):
    im = Image.open(path).convert('L')
    if resize:
        im = im.resize(resize, Image.BILINEAR)
    return np.asarray(im, dtype=np.float32) / 255.0

def ssim_simple(a,b):
    C1=0.01**2; C2=0.03**2
    mu1=a.mean(); mu2=b.mean()
    s1=a.var(); s2=b.var()
    s12 = ((a-mu1)*(b-mu2)).mean()
    den = (mu1*mu1 + mu2*mu2 + C1) * (s1 + s2 + C2)
    return ((2*mu1*mu2 + C1) * (2*s12 + C2)) / den if den!=0 else 0.0

def pairwise_similarity(imgs):
    N=len(imgs)
    S=np.zeros((N,N), dtype=np.float32)
    for i in range(N):
        for j in range(i+1,N):
            v = ssim_simple(imgs[i], imgs[j])
            S[i,j]=S[j,i]=v
    np.fill_diagonal(S, -1.0)
    return S

def greedy_nn(S):
    N=S.shape[0]
    start = int(np.argmax(S.sum(axis=1)))
    used = np.zeros(N, bool)
    order=[]
    cur = start
    for _ in range(N):
        order.append(cur)
        used[cur]=True
        row = S[cur].copy()
        row[used] = -1.0
        if np.all(row <= -1.0):
            break
        cur = int(np.argmax(row))
    if len(order)<N:
        for i in range(N):
            if not used[i]:
                order.append(i)
    return order

def two_opt(order,S,iter_limit=200):
    N=len(order)
    best=order[:]
    improved=True; it=0
    while improved and it<iter_limit:
        improved=False; it+=1
        for i in range(1,N-2):
            for j in range(i+1,N-1):
                a,b = best[i-1], best[i]
                c,d = best[j], best[j+1]
                old = S[a,b] + S[c,d]
                new = S[a,c] + S[b,d]
                if new > old + 1e-9:
                    best[i:j+1] = list(reversed(best[i:j+1]))
                    improved = True
    return best

def write_reordered(names, order, in_dir, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    ext = os.path.splitext(names[0])[1].lower()
    for k, idx in enumerate(order):
        src = os.path.join(in_dir, names[idx])
        dst = os.path.join(out_dir, f"frame{k:03d}{ext}")
        shutil.copyfile(src, dst)
    return ext

def write_list(out_list, out_dir, ext, n):
    with open(out_list,'w',encoding='utf-8') as f:
        for i in range(n):
            f.write(f"file '{out_dir}/frame{i:03d}{ext}'\n")

def main():
    frames_dir = "frames"
    names = list_frames(frames_dir)
    if len(names) == 0:
        print("No frames found in 'frames' folder.")
        return
    N = len(names)
    print("Found", N, "frames.")
    imgs = [load_gray(os.path.join(frames_dir, n), resize=(128,128)) for n in names]
    print("Computing similarity matrix...")
    S = pairwise_similarity(imgs)
    print("Greedy ordering...")
    order = greedy_nn(S)
    print("Optimizing (2-opt)...")
    order_opt = two_opt(order,S,iter_limit=300)

    def score(o):
        return sum(S[o[i], o[i+1]] for i in range(len(o)-1))
    if score(order_opt) >= score(order):
        order = order_opt

    fscore = score(order)
    rscore = score(order[::-1])
    if rscore > fscore:
        order = order[::-1]
        print("Automatically reversed order for smoother flow.")
    out_dir = "reordered"
    ext = write_reordered(names, order, frames_dir, out_dir)
    write_list("list.txt", out_dir, ext, N)
    print("Wrote 'reordered' and 'list.txt' (use ffmpeg to build).")

if __name__ == "__main__":
    main()
