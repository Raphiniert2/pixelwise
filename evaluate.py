from app.models import Prediction, SessionLocal
from collections import Counter

db = SessionLocal()
rows = db.query(Prediction).filter(Prediction.label.isnot(None)).all()
db.close()

total = len(rows)
correct = sum(1 for r in rows if r.label == r.prediction)
wrong = total - correct

print(f"Predictions mit Feedback: {total}")
print(f"Richtig: {correct}")
print(f"Falsch: {wrong}")
if total > 0:
    print(f"Accuracy: {correct / total * 100:.1f}%")

print("\nHäufigste Verwechslungen (Modell sagte X, war eigentlich Y):")
confusions = Counter(
    (r.prediction, r.label) for r in rows if r.label != r.prediction
)
for (pred, label), count in confusions.most_common(10):
    print(f"  Modell sagte {pred}, war eigentlich {label}: {count}x")
