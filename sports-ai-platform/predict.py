import pandas as pd
from sklearn.linear_model import LogisticRegression

# 從 CSV 載入資料
data = pd.read_csv(
    "data/mlb_games.csv"
)

X = data[
    [
        "home_win_rate",
        "away_win_rate",
        "home_rest_days",
        "away_rest_days"
    ]
]

y = data["result"]

model = LogisticRegression()
model.fit(X, y)

# 模擬新比賽
new_game = pd.DataFrame({
    "home_win_rate": [0.68],
    "away_win_rate": [0.55],
    "home_rest_days": [2],
    "away_rest_days": [1]
})

prob = model.predict_proba(new_game)[0]

print()
print("===== 預測結果 =====")
print(f"主隊勝率：{prob[1]:.2%}")
print(f"客隊勝率：{prob[0]:.2%}")