
book_summaries_dict = {
    "The Hobbit": (
        "Bilbo Baggins, un hobbit confortabil și fără aventuri, este luat prin surprindere "
        "atunci când este invitat într-o misiune de a recupera comoara piticilor păzită de "
        "dragonul Smaug. Pe parcursul călătoriei, el descoperă curajul și resursele "
        "interioare pe care nu știa că le are. Povestea este plină de creaturi fantastice, "
        "prieteni neașteptate și momente tensionate."
    ),
    "1984": (
        "Romanul lui George Orwell descrie o societate distopică aflată sub controlul total al "
        "statului. Oamenii sunt supravegheați constant de „Big Brother”, iar gândirea liberă "
        "este considerată crimă. Winston Smith, personajul principal, încearcă să reziste "
        "acestui regim opresiv. Este o poveste despre libertate, adevăr și manipulare ideologică."
    ),
    "To Kill a Mockingbird": (
        "Scout Finch, o fetiță din Alabama anilor 1930, trăiește prejudecățile și injustiția rasială din comunitatea ei. "
        "Tatăl ei, avocatul Atticus Finch, apără un bărbat de culoare acuzat pe nedrept de viol."
        " Romanul surprinde inocența, moralitatea și confruntarea cu răul social"
    ),
}

def get_summary_by_title(title: str) -> str:
    """
    Returnează rezumatul complet pentru un titlu exact, ignorând capitalizarea.
    Dacă nu există, returnează un mesaj de fallback.
    """
    title_lower = title.strip().lower()

    for key in book_summaries_dict:
        if key.lower() == title_lower:
            return book_summaries_dict[key]

    return f"Nu am găsit rezumat pentru titlul «{title}» în baza de date."
