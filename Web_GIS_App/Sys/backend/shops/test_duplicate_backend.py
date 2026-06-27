import os
import sys
import django

# Setup Django environment
sys.path.append('/home/quanghuy/DaiHoc/LuanVanTotNghiep/Web_GIS/Sys/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from shops.duplicate_checker import compute_similarity, _WEIGHTS as SCORE_WEIGHTS

duplicates = [
    ("Cafe Highland", "highlands coffee"),
    ("Trà sữa Phúc Long", "Phuc Long Tea & Coffee"),
    ("Phở 24h", "pho 24"),
    ("Gà Rán KFC", "KFC ga ran"),
    ("Siêu thị Coopmart", "co-op mart siêu thị"),
    ("Trạm xăng Petrolimex", "Cây xăng Petrolimex"),
    ("Nhà thuốc An Khang", "Nha Thuoc AN khang 12"),
    ("Bánh mì Huynh Hoa", "Bánh mỹ Huỳnh Hoa"),
    ("Tiệm cắt tóc 30Shine", "30 shine"),
    ("Rạp phim CGV", "CGV Cinemas"),
    ("Highland coffee", "Hiland cf"),
    ("Cửa hàng tiện lợi Circle K", "Circle K store"),
    ("Pizza Hut", "Piza hut"),
    ("Lotteria Nguyễn Trãi", "loteria nguyen trai"),
    ("Trung tâm thương mại Vincom", "Vincom center"),
    ("Jollibee", "Jolibee Fastfood"),
    ("Bún chả Hương Liên", "bun cha huong lien"),
    ("Kichi Kichi lẩu băng chuyền", "Lẩu kichi kichi"),
    ("Cộng Cà Phê", "Cong cafe"),
    ("Tạp hóa cô Tư", "Tạp hóa nhà cô Tư")
]

missed = []
detected = 0

for s1, s2 in duplicates:
    metrics = compute_similarity(s1, s2)
    weighted_score = (
        metrics['partial_ratio'] * SCORE_WEIGHTS['partial_ratio'] +
        metrics['token_set_ratio'] * SCORE_WEIGHTS['token_set_ratio'] +
        metrics['levenshtein_ratio'] * SCORE_WEIGHTS['levenshtein_ratio']
    )
    if weighted_score >= 0.8:
        detected += 1
    else:
        missed.append((s1, s2, weighted_score, metrics))

print(f"Nhận diện đúng: {detected}/{len(duplicates)}")
print(f"Bỏ sót: {len(missed)}/{len(duplicates)}")
for m in missed:
    print(f"MISS: {m[0]} vs {m[1]} -> Score: {m[2]:.2f} (Metrics: {m[3]})")
