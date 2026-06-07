def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_elo(rating_a, rating_b, result, k=20):
    expected_a = expected_score(rating_a, rating_b)

    rating_a_new = rating_a + k * (
        result - expected_a
    )

    rating_b_new = rating_b + k * (
        (1 - result) - (1 - expected_a)
    )

    return rating_a_new, rating_b_new


if __name__ == "__main__":

    team_a_rating = 1500
    team_b_rating = 1500

    new_a, new_b = update_elo(
        team_a_rating,
        team_b_rating,
        1
    )

    print(f"Team A Rating: {new_a}")
    print(f"Team B Rating: {new_b}")