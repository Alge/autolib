import autolib


def test_run_query():
    a = 92
    b = 15
    assert autolib.addTheseTwoNumbers(a, b) == a+b


def test_prime_numbers():
    assert autolib.GenerateTheNthPrimeNumber(24) == 89


def test_json_extraction():
    assert autolib.downloadJsonFromUrlAndReturnTheFieldTitle("https://hacker-news.firebaseio.com/v0/item/8863.json") == "My YC app: Dropbox - Throw away your USB drive"


