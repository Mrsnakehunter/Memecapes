// Mesh decimation for tools/glb2mdl.py --tris: quadric error, half-edge collapses, keeps texture UVs.
// Each collapse moves a vertex onto a neighbour, so every corner keeps a UV that already exists in
// its own texture chart (a collapse that would need a new UV is skipped). Borders are weighted to stay.
// build: g++ -O2 -o /tmp/decimate tools/decimate.cpp
// io (little-endian, stdin -> stdout): int nv, float pos[nv*3], int nf, int idx[nf*3], float uv[nf*3*2], int target
//                                      out: int nf, int idx[nf*3], float uv[nf*3*2]
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <queue>
#include <algorithm>
using namespace std;

struct Q { double a[10] = {0}; void add(const Q& o) { for (int i = 0; i < 10; i++) a[i] += o.a[i]; } };
static Q plane(double nx, double ny, double nz, double d, double w) {
    Q q; double p[4] = {nx, ny, nz, d}; int k = 0;
    for (int i = 0; i < 4; i++) for (int j = i; j < 4; j++) q.a[k++] = p[i] * p[j] * w;
    return q;
}
static double qerr(const Q& q, const double* v) {
    const double* a = q.a; double x = v[0], y = v[1], z = v[2];
    return a[0]*x*x + 2*a[1]*x*y + 2*a[2]*x*z + 2*a[3]*x + a[4]*y*y + 2*a[5]*y*z + 2*a[6]*y + a[7]*z*z + 2*a[8]*z + a[9];
}

int nv, nf;
vector<double> P; vector<int> F; vector<float> UV; vector<char> fdead, vdead;
vector<vector<int>> VF; vector<Q> VQ; vector<int> stamp;

struct E { double c; int u, v, su, sv; bool operator<(const E& o) const { return c > o.c; } };
priority_queue<E> heap;

static int corner(int f, int v) { for (int k = 0; k < 3; k++) if (F[f*3+k] == v) return k; return -1; }
static void fnorm(int a, int b, int c, double* n) {
    const double *A = &P[a*3], *B = &P[b*3], *C = &P[c*3];
    double e1[3] = {B[0]-A[0], B[1]-A[1], B[2]-A[2]}, e2[3] = {C[0]-A[0], C[1]-A[1], C[2]-A[2]};
    n[0] = e1[1]*e2[2]-e1[2]*e2[1]; n[1] = e1[2]*e2[0]-e1[0]*e2[2]; n[2] = e1[0]*e2[1]-e1[1]*e2[0];
}
static bool sameuv(const float* a, const float* b) { return fabs(a[0]-b[0]) < 1e-6 && fabs(a[1]-b[1]) < 1e-6; }

// can u move onto v?  fills the uv remap pairs (uv of u in a chart -> uv of v in that chart)
static bool valid(int u, int v, vector<float>& remap) {
    remap.clear();
    vector<int> nu, nvv, opp; int shared = 0;
    for (int f : VF[u]) if (!fdead[f]) {
        int ku = corner(f, u), kv = corner(f, v);
        for (int k = 0; k < 3; k++) if (F[f*3+k] != u) nu.push_back(F[f*3+k]);
        if (kv >= 0) { shared++; opp.push_back(F[f*3+3-ku-kv]);
            const float *a = &UV[(f*3+ku)*2], *b = &UV[(f*3+kv)*2];
            remap.insert(remap.end(), {a[0], a[1], b[0], b[1]}); }
    }
    if (shared == 0 || shared > 2) return false;
    for (int f : VF[v]) if (!fdead[f]) for (int k = 0; k < 3; k++) if (F[f*3+k] != v) nvv.push_back(F[f*3+k]);
    sort(nu.begin(), nu.end()); nu.erase(unique(nu.begin(), nu.end()), nu.end());
    sort(nvv.begin(), nvv.end()); nvv.erase(unique(nvv.begin(), nvv.end()), nvv.end());
    vector<int> common; set_intersection(nu.begin(), nu.end(), nvv.begin(), nvv.end(), back_inserter(common));
    sort(opp.begin(), opp.end()); opp.erase(unique(opp.begin(), opp.end()), opp.end());
    if (common != opp) return false;  // link condition: keeps the surface manifold
    for (int f : VF[u]) if (!fdead[f] && corner(f, v) < 0) {
        int ku = corner(f, u); int t[3] = {F[f*3], F[f*3+1], F[f*3+2]};
        double n0[3], n1[3]; fnorm(t[0], t[1], t[2], n0); t[ku] = v; fnorm(t[0], t[1], t[2], n1);
        double l0 = sqrt(n0[0]*n0[0]+n0[1]*n0[1]+n0[2]*n0[2]), l1 = sqrt(n1[0]*n1[0]+n1[1]*n1[1]+n1[2]*n1[2]);
        if (l1 < 1e-14) return false;
        if (l0 > 1e-14 && (n0[0]*n1[0]+n0[1]*n1[1]+n0[2]*n1[2]) / (l0*l1) < 0.3) return false;  // no flips
        const float* a = &UV[(f*3+ku)*2]; bool ok = false;
        for (size_t i = 0; i < remap.size(); i += 4) if (sameuv(a, &remap[i])) { ok = true; break; }
        if (!ok) return false;  // this chart does not reach v: the UV would have to be invented
    }
    return true;
}

static void pushv(int v) {
    vector<int> nb;
    for (int f : VF[v]) if (!fdead[f]) for (int k = 0; k < 3; k++) if (F[f*3+k] != v) nb.push_back(F[f*3+k]);
    sort(nb.begin(), nb.end()); nb.erase(unique(nb.begin(), nb.end()), nb.end());
    for (int n : nb) {
        Q q = VQ[v]; q.add(VQ[n]);
        heap.push({qerr(q, &P[n*3]), v, n, stamp[v], stamp[n]});
        heap.push({qerr(q, &P[v*3]), n, v, stamp[n], stamp[v]});
    }
}

template <class T> static void rd(T* p, size_t n) { if (fread(p, sizeof(T), n, stdin) != n) { fprintf(stderr, "short read\n"); exit(1); } }

int main() {
    rd(&nv, 1); vector<float> pf(nv*3); rd(pf.data(), pf.size()); P.assign(pf.begin(), pf.end());
    rd(&nf, 1); F.resize(nf*3); rd(F.data(), F.size()); UV.resize(nf*6); rd(UV.data(), UV.size());
    int target; rd(&target, 1);
    fdead.assign(nf, 0); vdead.assign(nv, 0); VF.resize(nv); VQ.resize(nv); stamp.assign(nv, 0);
    for (int f = 0; f < nf; f++) {
        int a = F[f*3], b = F[f*3+1], c = F[f*3+2];
        if (a == b || b == c || a == c) { fdead[f] = 1; continue; }
        for (int k = 0; k < 3; k++) VF[F[f*3+k]].push_back(f);
        double n[3]; fnorm(a, b, c, n); double l = sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]); if (l < 1e-18) continue;
        for (int i = 0; i < 3; i++) n[i] /= l;
        Q q = plane(n[0], n[1], n[2], -(n[0]*P[a*3]+n[1]*P[a*3+1]+n[2]*P[a*3+2]), l * .5);
        for (int k = 0; k < 3; k++) VQ[F[f*3+k]].add(q);
    }
    // border edges (used by one face): a steep plane through the edge, across the face
    {
        vector<pair<long long,int>> ed;
        for (int f = 0; f < nf; f++) if (!fdead[f]) for (int k = 0; k < 3; k++) {
            int a = F[f*3+k], b = F[f*3+(k+1)%3]; ed.push_back({(long long)min(a,b) * nv + max(a,b), f*3+k}); }
        sort(ed.begin(), ed.end());
        for (size_t i = 0; i < ed.size(); ) {
            size_t j = i; while (j < ed.size() && ed[j].first == ed[i].first) j++;
            if (j - i == 1) {
                int f = ed[i].second / 3, k = ed[i].second % 3, a = F[f*3+k], b = F[f*3+(k+1)%3];
                double n[3]; fnorm(F[f*3], F[f*3+1], F[f*3+2], n);
                double e[3] = {P[b*3]-P[a*3], P[b*3+1]-P[a*3+1], P[b*3+2]-P[a*3+2]};
                double m[3] = {e[1]*n[2]-e[2]*n[1], e[2]*n[0]-e[0]*n[2], e[0]*n[1]-e[1]*n[0]};
                double l = sqrt(m[0]*m[0]+m[1]*m[1]+m[2]*m[2]);
                if (l > 1e-18) { for (int t = 0; t < 3; t++) m[t] /= l;
                    double el = e[0]*e[0]+e[1]*e[1]+e[2]*e[2];
                    Q q = plane(m[0], m[1], m[2], -(m[0]*P[a*3]+m[1]*P[a*3+1]+m[2]*P[a*3+2]), el * 20);
                    VQ[a].add(q); VQ[b].add(q); }
            }
            i = j;
        }
    }
    int alive = 0; for (int f = 0; f < nf; f++) alive += !fdead[f];
    for (int v = 0; v < nv; v++) pushv(v);
    vector<float> remap;
    while (alive > target && !heap.empty()) {
        E e = heap.top(); heap.pop();
        int u = e.u, v = e.v;
        if (vdead[u] || vdead[v] || stamp[u] != e.su || stamp[v] != e.sv) continue;
        if (!valid(u, v, remap)) continue;
        for (int f : VF[u]) if (!fdead[f]) {
            int ku = corner(f, u);
            if (corner(f, v) >= 0) { fdead[f] = 1; alive--; continue; }
            float* a = &UV[(f*3+ku)*2];
            for (size_t i = 0; i < remap.size(); i += 4) if (sameuv(a, &remap[i])) { a[0] = remap[i+2]; a[1] = remap[i+3]; break; }
            F[f*3+ku] = v; VF[v].push_back(f);
        }
        vdead[u] = 1; VQ[v].add(VQ[u]); stamp[v]++;
        vector<int> keep; for (int f : VF[v]) if (!fdead[f]) keep.push_back(f);
        sort(keep.begin(), keep.end()); keep.erase(unique(keep.begin(), keep.end()), keep.end()); VF[v] = keep;
        pushv(v);
    }
    int out = 0; for (int f = 0; f < nf; f++) out += !fdead[f];
    fwrite(&out, 4, 1, stdout);
    for (int f = 0; f < nf; f++) if (!fdead[f]) fwrite(&F[f*3], 4, 3, stdout);
    for (int f = 0; f < nf; f++) if (!fdead[f]) fwrite(&UV[f*6], 4, 6, stdout);
    fprintf(stderr, "decimate: %d -> %d faces\n", nf, out);
    return 0;
}
