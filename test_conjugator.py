"""Tests for the conjugator against known-correct forms.

Run: python test_conjugator.py
"""
from conjugator import conjugate, split_verb, conj_present, conj_past, \
    conj_future, conj_aorist

CASES = {
    # verb: (present, past, future, aorist) — each a 6-tuple ben..onlar
    "gitmek": (
        ["gidiyorum", "gidiyorsun", "gidiyor", "gidiyoruz", "gidiyorsunuz", "gidiyorlar"],
        ["gittim", "gittin", "gitti", "gittik", "gittiniz", "gittiler"],
        ["gideceğim", "gideceksin", "gidecek", "gideceğiz", "gideceksiniz", "gidecekler"],
        ["giderim", "gidersin", "gider", "gideriz", "gidersiniz", "giderler"],
    ),
    "etmek": (
        ["ediyorum", "ediyorsun", "ediyor", "ediyoruz", "ediyorsunuz", "ediyorlar"],
        ["ettim", "ettin", "etti", "ettik", "ettiniz", "ettiler"],
        ["edeceğim", "edeceksin", "edecek", "edeceğiz", "edeceksiniz", "edecekler"],
        ["ederim", "edersin", "eder", "ederiz", "edersiniz", "ederler"],
    ),
    "demek": (
        ["diyorum", "diyorsun", "diyor", "diyoruz", "diyorsunuz", "diyorlar"],
        ["dedim", "dedin", "dedi", "dedik", "dediniz", "dediler"],
        ["diyeceğim", "diyeceksin", "diyecek", "diyeceğiz", "diyeceksiniz", "diyecekler"],
        ["derim", "dersin", "der", "deriz", "dersiniz", "derler"],
    ),
    "yemek": (
        ["yiyorum", "yiyorsun", "yiyor", "yiyoruz", "yiyorsunuz", "yiyorlar"],
        ["yedim", "yedin", "yedi", "yedik", "yediniz", "yediler"],
        ["yiyeceğim", "yiyeceksin", "yiyecek", "yiyeceğiz", "yiyeceksiniz", "yiyecekler"],
        ["yerim", "yersin", "yer", "yeriz", "yersiniz", "yerler"],
    ),
    "olmak": (
        ["oluyorum", "oluyorsun", "oluyor", "oluyoruz", "oluyorsunuz", "oluyorlar"],
        ["oldum", "oldun", "oldu", "olduk", "oldunuz", "oldular"],
        ["olacağım", "olacaksın", "olacak", "olacağız", "olacaksınız", "olacaklar"],
        ["olurum", "olursun", "olur", "oluruz", "olursunuz", "olurlar"],
    ),
    "başlamak": (
        ["başlıyorum", "başlıyorsun", "başlıyor", "başlıyoruz", "başlıyorsunuz", "başlıyorlar"],
        ["başladım", "başladın", "başladı", "başladık", "başladınız", "başladılar"],
        ["başlayacağım", "başlayacaksın", "başlayacak", "başlayacağız", "başlayacaksınız", "başlayacaklar"],
        ["başlarım", "başlarsın", "başlar", "başlarız", "başlarsınız", "başlarlar"],
    ),
    "oynamak": (
        ["oynuyorum", "oynuyorsun", "oynuyor", "oynuyoruz", "oynuyorsunuz", "oynuyorlar"],
        ["oynadım", "oynadın", "oynadı", "oynadık", "oynadınız", "oynadılar"],
        ["oynayacağım", "oynayacaksın", "oynayacak", "oynayacağız", "oynayacaksınız", "oynayacaklar"],
        ["oynarım", "oynarsın", "oynar", "oynarız", "oynarsınız", "oynarlar"],
    ),
    "söylemek": (
        ["söylüyorum", "söylüyorsun", "söylüyor", "söylüyoruz", "söylüyorsunuz", "söylüyorlar"],
        ["söyledim", "söyledin", "söyledi", "söyledik", "söylediniz", "söylediler"],
        ["söyleyeceğim", "söyleyeceksin", "söyleyecek", "söyleyeceğiz", "söyleyeceksiniz", "söyleyecekler"],
        ["söylerim", "söylersin", "söyler", "söyleriz", "söylersiniz", "söylerler"],
    ),
    "okumak": (
        ["okuyorum", "okuyorsun", "okuyor", "okuyoruz", "okuyorsunuz", "okuyorlar"],
        ["okudum", "okudun", "okudu", "okuduk", "okudunuz", "okudular"],
        ["okuyacağım", "okuyacaksın", "okuyacak", "okuyacağız", "okuyacaksınız", "okuyacaklar"],
        ["okurum", "okursun", "okur", "okuruz", "okursunuz", "okurlar"],
    ),
    "tatmak": (
        ["tadıyorum", "tadıyorsun", "tadıyor", "tadıyoruz", "tadıyorsunuz", "tadıyorlar"],
        ["tattım", "tattın", "tattı", "tattık", "tattınız", "tattılar"],
        ["tadacağım", "tadacaksın", "tadacak", "tadacağız", "tadacaksınız", "tadacaklar"],
        ["tadarım", "tadarsın", "tadar", "tadarız", "tadarsınız", "tadarlar"],
    ),
    "hissetmek": (
        ["hissediyorum", "hissediyorsun", "hissediyor", "hissediyoruz", "hissediyorsunuz", "hissediyorlar"],
        ["hissettim", "hissettin", "hissetti", "hissettik", "hissettiniz", "hissettiler"],
        ["hissedeceğim", "hissedeceksin", "hissedecek", "hissedeceğiz", "hissedeceksiniz", "hissedecekler"],
        ["hissederim", "hissedersin", "hisseder", "hissederiz", "hissedersiniz", "hissederler"],
    ),
    "gelmek": (
        ["geliyorum", "geliyorsun", "geliyor", "geliyoruz", "geliyorsunuz", "geliyorlar"],
        ["geldim", "geldin", "geldi", "geldik", "geldiniz", "geldiler"],
        ["geleceğim", "geleceksin", "gelecek", "geleceğiz", "geleceksiniz", "gelecekler"],
        ["gelirim", "gelirsin", "gelir", "geliriz", "gelirsiniz", "gelirler"],
    ),
    "yapmak": (
        ["yapıyorum", "yapıyorsun", "yapıyor", "yapıyoruz", "yapıyorsunuz", "yapıyorlar"],
        ["yaptım", "yaptın", "yaptı", "yaptık", "yaptınız", "yaptılar"],
        ["yapacağım", "yapacaksın", "yapacak", "yapacağız", "yapacaksınız", "yapacaklar"],
        ["yaparım", "yaparsın", "yapar", "yaparız", "yaparsınız", "yaparlar"],
    ),
    "görmek": (
        ["görüyorum", "görüyorsun", "görüyor", "görüyoruz", "görüyorsunuz", "görüyorlar"],
        ["gördüm", "gördün", "gördü", "gördük", "gördünüz", "gördüler"],
        ["göreceğim", "göreceksin", "görecek", "göreceğiz", "göreceksiniz", "görecekler"],
        ["görürüm", "görürsün", "görür", "görürüz", "görürsünüz", "görürler"],
    ),
    "konuşmak": (
        ["konuşuyorum", "konuşuyorsun", "konuşuyor", "konuşuyoruz", "konuşuyorsunuz", "konuşuyorlar"],
        ["konuştum", "konuştun", "konuştu", "konuştuk", "konuştunuz", "konuştular"],
        ["konuşacağım", "konuşacaksın", "konuşacak", "konuşacağız", "konuşacaksınız", "konuşacaklar"],
        ["konuşurum", "konuşursun", "konuşur", "konuşuruz", "konuşursunuz", "konuşurlar"],
    ),
    "gülümsemek": (
        ["gülümsüyorum", "gülümsüyorsun", "gülümsüyor", "gülümsüyoruz", "gülümsüyorsunuz", "gülümsüyorlar"],
        ["gülümsedim", "gülümsedin", "gülümsedi", "gülümsedik", "gülümsediniz", "gülümsediler"],
        ["gülümseyeceğim", "gülümseyeceksin", "gülümseyecek", "gülümseyeceğiz", "gülümseyeceksiniz", "gülümseyecekler"],
        ["gülümserim", "gülümsersin", "gülümser", "gülümseriz", "gülümsersiniz", "gülümserler"],
    ),
    "kapatmak": (
        ["kapatıyorum", "kapatıyorsun", "kapatıyor", "kapatıyoruz", "kapatıyorsunuz", "kapatıyorlar"],
        ["kapattım", "kapattın", "kapattı", "kapattık", "kapattınız", "kapattılar"],
        ["kapatacağım", "kapatacaksın", "kapatacak", "kapatacağız", "kapatacaksınız", "kapatacaklar"],
        ["kapatırım", "kapatırsın", "kapatır", "kapatırız", "kapatırsınız", "kapatırlar"],
    ),
    "bırakmak": (
        ["bırakıyorum", "bırakıyorsun", "bırakıyor", "bırakıyoruz", "bırakıyorsunuz", "bırakıyorlar"],
        ["bıraktım", "bıraktın", "bıraktı", "bıraktık", "bıraktınız", "bıraktılar"],
        ["bırakacağım", "bırakacaksın", "bırakacak", "bırakacağız", "bırakacaksınız", "bırakacaklar"],
        ["bırakırım", "bırakırsın", "bırakır", "bırakırız", "bırakırsınız", "bırakırlar"],
    ),
    "yürümek": (
        ["yürüyorum", "yürüyorsun", "yürüyor", "yürüyoruz", "yürüyorsunuz", "yürüyorlar"],
        ["yürüdüm", "yürüdün", "yürüdü", "yürüdük", "yürüdünüz", "yürüdüler"],
        ["yürüyeceğim", "yürüyeceksin", "yürüyecek", "yürüyeceğiz", "yürüyeceksiniz", "yürüyecekler"],
        ["yürürüm", "yürürsün", "yürür", "yürürüz", "yürürsünüz", "yürürler"],
    ),
    "almak": (
        ["alıyorum", "alıyorsun", "alıyor", "alıyoruz", "alıyorsunuz", "alıyorlar"],
        ["aldım", "aldın", "aldı", "aldık", "aldınız", "aldılar"],
        ["alacağım", "alacaksın", "alacak", "alacağız", "alacaksınız", "alacaklar"],
        ["alırım", "alırsın", "alır", "alırız", "alırsınız", "alırlar"],
    ),
}

COMPOUND_CASES = {
    "yardım etmek": ("yardım ediyorum", "yardım etti", "yardım edeceğim", "yardım ederler"),
    "karar vermek": ("karar veriyorum", "karar verdi", "karar vereceğim", "karar verirler"),
}


def main():
    failures = 0
    for verb, (pres, past, fut, aor) in CASES.items():
        _, stem = split_verb(verb)
        for name, expected, fn in [("present", pres, conj_present),
                                   ("past", past, conj_past),
                                   ("future", fut, conj_future),
                                   ("aorist", aor, conj_aorist)]:
            got = fn(stem)
            if got != expected:
                failures += 1
                print(f"FAIL {verb} {name}:\n  expected {expected}\n  got      {got}")
    for verb, (p0, pa2, f0, a5) in COMPOUND_CASES.items():
        t = conjugate(verb)
        forms = list(t.values())
        checks = [(forms[0][0], p0), (forms[1][2], pa2),
                  (forms[2][0], f0), (forms[3][5], a5)]
        for got, expected in checks:
            if got != expected:
                failures += 1
                print(f"FAIL {verb}: expected {expected!r}, got {got!r}")
    total = len(CASES) * 4 + len(COMPOUND_CASES) * 4
    print(f"{total - failures}/{total} checks passed")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
