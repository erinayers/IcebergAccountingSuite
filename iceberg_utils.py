import string
import random
from decimal import Decimal as dec

import iceberg_time


def get_current_time_info():
    """Returns ``(display_time, display_timestamp)`` for the local timezone.

    Both strings use the neutral ``UTC+hh:mm`` offset instead of a localized
    zone name.  See ``iceberg_time`` for the storage format used in databases.
    """
    return iceberg_time.get_current_time_info()


def format_currency(integer, symbol="$"):
    """Converts an integer number of cents to currency format (string) without a dollar sign (2 digits after the decimal)"""
    initial_string = f"{int(integer)}"
    # print(initial_string)
    final_string = ""
    if int(integer) == 0 or integer == "0":
        final_string = f"{symbol}0.00"
    elif initial_string[0] == "-":

        if len(initial_string) >= 5:
            no_commas = (
                f"({int(integer)*(-1)}"[:-2] + "." + f"{(int(integer)*(-1))}"[-2:] + ")"
            )

            count = 0
            for i in range(len(no_commas)):
                if (
                    no_commas[len(no_commas) - i - 1] != ")"
                    and no_commas[len(no_commas) - i - 1] != "("
                    and no_commas[len(no_commas) - i - 1] != "."
                ):

                    count = count + 1

                elif no_commas[len(no_commas) - i - 1] == ".":
                    count = 0

                if no_commas[len(no_commas) - i - 1] == "(":
                    final_string = (
                        no_commas[len(no_commas) - i - 1] + symbol + final_string
                    )

                elif count < 4:
                    final_string = no_commas[len(no_commas) - i - 1] + final_string
                elif count == 4:
                    count = 1
                    final_string = (
                        no_commas[len(no_commas) - i - 1] + "," + final_string
                    )
        elif len(initial_string) == 3:
            final_string = f"({symbol}0.{initial_string[1:]})"
        elif len(initial_string) == 4:
            final_string = f"({symbol}{initial_string[1:-2]}.{initial_string[-2:]})"
        elif len(initial_string) == 2:
            final_string = f"({symbol}0.0{initial_string[1:]})"

    else:

        no_commas = f"{int(integer)}"[:-2] + f"{(int(integer)*(-1))}"[-2:]
        if len(initial_string) >= 3:
            no_commas = f"{int(integer)}"[:-2] + "." + f"{(int(integer)*(-1))}"[-2:]
            count = 0
            for i in range(len(no_commas)):
                if no_commas[len(no_commas) - i - 1] != ".":
                    count = count + 1

                elif no_commas[len(no_commas) - i - 1] == ".":
                    count = 0

                if count < 4:
                    final_string = no_commas[len(no_commas) - i - 1] + final_string
                elif count == 4:
                    count = 1
                    final_string = (
                        no_commas[len(no_commas) - i - 1] + "," + final_string
                    )
            final_string = symbol + final_string
        elif len(initial_string) == 2:
            final_string = f"{symbol}0.{int(integer)}"
        elif len(initial_string) == 1:
            final_string = f"{symbol}0.0{int(integer)}"

    # print(final_string)
    return final_string


def convert_dollars_to_cents(dollars):
    """Return cents for a dollar string, or None when it is not a number."""
    text = f"{dollars}".replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return int(dec(text) * 100)
    except Exception:
        return None


def id_generator(size=30, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))
