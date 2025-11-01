#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define HIST_BINS 256


static inline unsigned char rgb_to_luma(unsigned char r, unsigned char g, unsigned char b) {
    float yf = 0.299f * r + 0.587f * g + 0.114f * b;
    int y = (int)(yf + 0.5f);
    if (y < 0) y = 0;
    if (y > 255) y = 255;
    return (unsigned char)y;
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <frames_dir> <num_frames> <out_list_txt>\n", argv[0]);
        return 1;
    }
    char *dir = argv[1];
    int N = atoi(argv[2]);
    char *out_list = argv[3];
    if (N <= 0) {
        fprintf(stderr, "Invalid number of frames: %d\n", N);
        return 1;
    }
    double **hist = (double**)malloc(sizeof(double*) * N);
    if (!hist) { perror("malloc"); return 1; }
    for (int i = 0; i < N; ++i) {
        hist[i] = (double*)calloc(HIST_BINS, sizeof(double));
        if (!hist[i]) { perror("calloc"); return 1; }
    }


    for (int i = 0; i < N; ++i) {
        char fname[1024];
        snprintf(fname, sizeof(fname), "%s/frame%03d.png", dir, i);
        int w, h, channels;
        unsigned char *img = stbi_load(fname, &w, &h, &channels, 3);
        if (!img) {
            fprintf(stderr, "Failed to load %s (check filename/format). Exiting.\n", fname);
            return 2;
        }
        long long total = (long long)w * h;

        for (long long p = 0; p < total; ++p) {
            unsigned char r = img[p*3 + 0];
            unsigned char g = img[p*3 + 1];
            unsigned char b = img[p*3 + 2];
            unsigned char y = rgb_to_luma(r,g,b);
            hist[i][y] += 1.0;
        }

        for (int b = 0; b < HIST_BINS; ++b) hist[i][b] /= (double)total;
        stbi_image_free(img);

        if ((i & 31) == 0) {
            printf("Loaded %d/%d\n", i+1, N);
            fflush(stdout);
        }
    }

    double *distmat = (double*)malloc(sizeof(double) * N * N);
    if (!distmat) { perror("malloc distmat"); return 1; }
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            if (i == j) { distmat[i*N + j] = 0.0; continue; }
            double s = 0.0;
            for (int b = 0; b < HIST_BINS; ++b) {
                double d = hist[i][b] - hist[j][b];
                s += d * d;
            }
            distmat[i*N + j] = sqrt(s);
        }
    }

    int start = 0;
    double best_sum = 1e300;
    for (int i = 0; i < N; ++i) {
        double sum = 0.0;
        for (int j = 0; j < N; ++j) sum += distmat[i*N + j];
        if (sum < best_sum) { best_sum = sum; start = i; }
    }
    printf("Starting frame chosen: %d (avgDist=%.6f)\n", start, best_sum);

    int *used = (int*)calloc(N, sizeof(int));
    int *order = (int*)malloc(sizeof(int) * N);
    int cur = start;
    for (int k = 0; k < N; ++k) {
        order[k] = cur;
        used[cur] = 1;

        int best_j = -1;
        double best_d = 1e300;
        for (int j = 0; j < N; ++j) {
            if (used[j]) continue;
            double d = distmat[cur*N + j];
            if (d < best_d) { best_d = d; best_j = j; }
        }
        if (best_j == -1) break;
        cur = best_j;
    }

    int used_count = 0;
    for (int i = 0; i < N; ++i) if (used[i]) used_count++;
    if (used_count < N) {
        for (int i = 0; i < N; ++i) {
            if (!used[i]) {
                order[used_count++] = i;
            }
        }
    }

    FILE *f = fopen(out_list, "w");
    if (!f) { perror("fopen out_list"); return 1; }
    for (int k = 0; k < N; ++k) {
        int idx = order[k];
        fprintf(f, "file '%s/frame%03d.png'\n", dir, idx);
    }
    fclose(f);
    printf("Wrote %s with %d entries.\n", out_list, N);

    FILE *fo = fopen("ordered_list.txt", "w");
    if (fo) {
        for (int k = 0; k < N; ++k) fprintf(fo, "%03d -> frame%03d.png\n", k, order[k]);
        fclose(fo);
    }


    for (int i = 0; i < N; ++i) free(hist[i]);
    free(hist);
    free(distmat);
    free(used);
    free(order);

    printf("Done.\n");
    return 0;
}
