"""Turkish verb conjugator.

Generates full conjugation tables from an infinitive using the regular
rules of Turkish morphology:

- 2-way vowel harmony (e/a) and 4-way vowel harmony (i/ı/u/ü)
- consonant voicing t -> d for the small irregular set (gitmek, etmek,
  tatmak, gütmek, ditmek) and single-word etmek compounds (hissetmek,
  kaybetmek, ...)
- stem-final a/e narrowing before -(I)yor (başla- -> başlıyor)
- the special de-/ye- narrowing in the future (diyecek, yiyecek)
- the aorist's monosyllabic exceptions (gelir, alır, ...)

Compound verbs written as two words (yardım etmek, karar vermek) are
conjugated on their last word.
"""

VOWELS = "aeıioöuü"
FRONT = "eiöü"
ROUNDED = "ouöü"
VOICELESS = "fstkçşhp"

# stems whose final t voices to d before a vowel-initial suffix
T_VOICING = {"git", "et", "tat", "güt", "dit"}
# single-word etmek compounds: conjugate like etmek (aorist -er, voicing)
ET_COMPOUNDS = {"et", "hisset", "kaybet", "kaydet", "seyret", "affet",
                "bahset", "zannet", "reddet", "hallet"}
# monosyllabic stems whose aorist takes a narrow vowel (gel-ir, not *gel-er)
AORIST_NARROW = {"al", "bil", "bul", "dur", "gel", "gör", "kal", "ol",
                 "öl", "san", "var", "ver", "vur"}

PERSONS = ["ben", "sen", "o", "biz", "siz", "onlar"]


def last_vowel(s):
    for ch in reversed(s):
        if ch in VOWELS:
            return ch
    return None


def vowel_count(s):
    return sum(1 for ch in s if ch in VOWELS)


def h2(v):
    """2-way harmony: e or a."""
    return "e" if v in FRONT else "a"


def h4(v):
    """4-way harmony: i, ı, u or ü."""
    if v in FRONT:
        return "ü" if v in ROUNDED else "i"
    return "u" if v in ROUNDED else "ı"


def split_verb(infinitive):
    """'yardım etmek' -> ('yardım', 'et')"""
    parts = infinitive.strip().split()
    inf = parts[-1]
    if not inf.endswith(("mak", "mek")):
        raise ValueError(f"not an infinitive: {infinitive!r}")
    return " ".join(parts[:-1]), inf[:-3]


def voiced(stem):
    if stem in T_VOICING or stem in ET_COMPOUNDS:
        return stem[:-1] + "d"
    return stem


def present_continuous(stem):
    """Base form: gidiyor, başlıyor, oynuyor, diyor..."""
    s = voiced(stem)
    if s[-1] in "ae":
        # drop the final wide vowel, replace with narrow vowel:
        # frontness from the dropped vowel, rounding from the previous one
        base, dropped = s[:-1], s[-1]
        prev = last_vowel(base)
        if dropped == "e":
            v = "ü" if (prev and prev in ROUNDED) else "i"
        else:
            v = "u" if (prev and prev in ROUNDED) else "ı"
        return base + v + "yor"
    if s[-1] in VOWELS:  # already narrow: oku- -> okuyor
        return s + "yor"
    return s + h4(last_vowel(s)) + "yor"


def conj_present(stem):
    b = present_continuous(stem)
    return [b + "um", b + "sun", b, b + "uz", b + "sunuz", b + "lar"]


def conj_past(stem):
    v = h4(last_vowel(stem))
    d = "t" if stem[-1] in VOICELESS else "d"
    b = stem + d + v
    plural = "ler" if h2(last_vowel(stem)) == "e" else "lar"
    return [b + "m", b + "n", b, b + "k", b + "n" + v + "z", b + plural]


def future_base(stem):
    if stem == "de":
        s = "di"
    elif stem == "ye":
        s = "yi"
    else:
        s = voiced(stem)
    front = h2(last_vowel(stem)) == "e"
    if s[-1] in VOWELS:
        return s + ("yecek" if front else "yacak")
    return s + ("ecek" if front else "acak")


def conj_future(stem):
    b = future_base(stem)
    front = b.endswith("ecek")
    i, plural = ("i", "ler") if front else ("ı", "lar")
    soft = b[:-1] + "ğ"  # gelecek -> geleceğ-
    return [soft + i + "m", b + "s" + i + "n", b,
            soft + i + "z", b + "s" + i + "n" + i + "z", b + plural]


def aorist_base(stem):
    s = voiced(stem)
    if stem in ET_COMPOUNDS:
        return s + ("er" if h2(last_vowel(stem)) == "e" else "ar")
    if s[-1] in VOWELS:
        return s + "r"
    if stem in AORIST_NARROW:
        return s + h4(last_vowel(s)) + "r"
    if vowel_count(stem) == 1:
        return s + h2(last_vowel(s)) + "r"
    return s + h4(last_vowel(s)) + "r"


def conj_aorist(stem):
    b = aorist_base(stem)
    v = h4(last_vowel(b))
    plural = "ler" if h2(last_vowel(b)) == "e" else "lar"
    return [b + v + "m", b + "s" + v + "n", b,
            b + v + "z", b + "s" + v + "n" + v + "z", b + plural]


TENSES = [
    ("Şimdiki zaman", "present continuous", conj_present),
    ("Geçmiş zaman", "simple past", conj_past),
    ("Gelecek zaman", "future", conj_future),
    ("Geniş zaman", "aorist / habitual", conj_aorist),
]


def conjugate(infinitive):
    """Return {tense_name: [6 forms with 'ben/sen/...' order]}."""
    head, stem = split_verb(infinitive)
    prefix = head + " " if head else ""
    out = {}
    for tr_name, en_name, fn in TENSES:
        out[(tr_name, en_name)] = [prefix + f for f in fn(stem)]
    return out
