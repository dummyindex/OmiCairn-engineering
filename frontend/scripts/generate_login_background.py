"""Generate the synthetic point cloud used as the decorative login-page background.

The file is purely synthetic (Gaussian clusters with generic labels); it contains no
real cells, samples or donors. Run from the frontend directory:

    python scripts/generate_login_background.py > public/test_dataset.csv
"""
import random

CLUSTERS = [
    ("Cluster A", (0.0, 8.0, 7.5), 0.9, 2400),
    ("Cluster B", (6.0, 3.0, 5.0), 1.1, 2000),
    ("Cluster C", (-5.0, 2.0, 6.5), 0.8, 1600),
    ("Cluster D", (2.0, -4.0, 4.0), 1.0, 1200),
    ("Cluster E", (-2.0, -1.0, 9.0), 0.7, 800),
]


def main(seed: int = 0) -> None:
    rng = random.Random(seed)
    print(",celltype,UMAP_0,UMAP_1,UMAP_2")
    idx = 0
    for label, (cx, cy, cz), sd, n in CLUSTERS:
        for _ in range(n):
            x, y, z = (rng.gauss(c, sd) for c in (cx, cy, cz))
            print(f"cell_{idx},{label},{x:.5f},{y:.5f},{z:.5f}")
            idx += 1


if __name__ == "__main__":
    main()
