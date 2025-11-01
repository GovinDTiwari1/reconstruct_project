import sys, os, shutil
import numpy as np
from PIL import Image

def ssim(img1, img2):
    C1 = 0.01 ** 2
    C2 = 0.03 ** 2
    mu1 = img1.mean()
    mu2 = img2.mean()
    sigma1 = img1.var()
    sigma2 = img2.var()
    sigma12 = ((img1 - mu1) * (img2 - mu2)).mean()
    return ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / ((mu1**2 + mu2**2 + C1) * (sigma1 + sigma2 + C2))

def load_gray(path):
    return np.asarray(Image.open(path).convert('L'), dtype=np.float32)

def main():
    if len(sys.argv) < 4:
        print("Usage: python reorder_frames_ssim.py <frames_dir> <num_frames> <out_list.txt>")
        return
    frames_dir, N, out_list = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    files = sorted([f for f in os.listdir(frames_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))])[:N]
    imgs = [load_gray(os.path.join(frames_dir,f)) for f in files]
    imgs = [Image.fromarray(i).resize((64,64)) for i in imgs]
    imgs = [np.asarray(i,dtype=np.float32)/255. for i in imgs]
    N = len(imgs)
    print(f"Computing SSIM matrix for {N} frames...")
    sim = np.zeros((N,N),dtype=np.float32)
    for i in range(N):
        for j in range(i+1,N):
            v = ssim(imgs[i], imgs[j])
            sim[i,j]=sim[j,i]=v
        if (i+1)%20==0: print(i+1,"/",N)
    avg = sim.mean(1)
    cur = int(np.argmax(avg))
    used=np.zeros(N,bool)
    order=[]
    for _ in range(N):
        order.append(cur)
        used[cur]=True
        sims=sim[cur].copy(); sims[used]=-1
        if np.all(sims<0): break
        cur=int(np.argmax(sims))

    # ✅ Direction fix: check which direction gives smoother SSIM sequence
    def seq_score(seq):
        s = 0
        for i in range(len(seq)-1):
            s += sim[seq[i], seq[i+1]]
        return s
    forward_score = seq_score(order)
    reverse_score = seq_score(order[::-1])
    if reverse_score > forward_score:
        order = order[::-1]
        print("Reversed order for smoother temporal flow ✅")

    out_dir="reordered"
    if os.path.exists(out_dir): shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    ext=os.path.splitext(files[0])[1]
    for k,idx in enumerate(order):
        shutil.copyfile(os.path.join(frames_dir,files[idx]), os.path.join(out_dir,f"frame{k:03d}{ext}"))
    with open(out_list,'w') as f:
        for k in range(len(order)):
            f.write(f"file 'reordered/frame{k:03d}{ext}'\n")
    print("Done -> reordered/, list:", out_list)

if __name__=="__main__":
    main()
