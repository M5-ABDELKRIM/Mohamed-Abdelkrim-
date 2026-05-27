import argparse
import os
from itertools import product

import pandas as pd


UPPERCASE_LETTERS = {"A", "B", "C", "D", "E"}
LOWERCASE_LETTERS = {"a", "b", "c", "d", "e"}
DIGITS = {"1", "2", "3", "4", "5"}
SPECIAL_SYMBOLS = {"$", "&", "%"}


def is_valid_password(password):
    password_list = list(password)

    if not any(char in UPPERCASE_LETTERS for char in password_list):
        return False
    if not any(char in LOWERCASE_LETTERS for char in password_list):
        return False
    if not any(char in DIGITS for char in password_list):
        return False
    if not any(char in SPECIAL_SYMBOLS for char in password_list):
        return False
    if password_list[0] not in UPPERCASE_LETTERS and password_list[0] not in LOWERCASE_LETTERS:
        return False
    if sum(char in UPPERCASE_LETTERS for char in password_list) > 2:
        return False
    if sum(char in SPECIAL_SYMBOLS for char in password_list) > 2:
        return False

    return True


def generate_valid_passwords(length):
    character_set = UPPERCASE_LETTERS | LOWERCASE_LETTERS | DIGITS | SPECIAL_SYMBOLS
    all_possible_passwords = product(character_set, repeat=length)
    return ["".join(password) for password in all_possible_passwords if is_valid_password(password)]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate passwords that satisfy the coursework rules.")
    parser.add_argument("length", nargs="?", type=int, help="Password length to generate")
    return parser.parse_args()


def main():
    args = parse_args()
    password_length = args.length or int(input("Enter the password length: "))
    valid_passwords = generate_valid_passwords(password_length)

    password_df = pd.DataFrame(
        {"Index": range(1, len(valid_passwords) + 1), "Password": valid_passwords}
    )

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "valid_passwords.csv")

    password_df.to_csv(output_path, index=False)
    print(f"Valid passwords saved to: {output_path}")
    print(password_df.head(10))


if __name__ == "__main__":
    main()
