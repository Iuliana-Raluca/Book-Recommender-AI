import base64
import io
from openai import OpenAI
import tempfile
from pathlib import Path

client = OpenAI()

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



def generate_book_cover(title: str):
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",  
            input=f"Generate an image of a book cover for the novel titled '{title}', in a literary style.",
            tools=[{"type": "image_generation"}],
        )

        image_data = [
            output.result
            for output in response.output
            if output.type == "image_generation_call"
        ]

        if image_data:
            image_base64 = image_data[0]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                f.write(base64.b64decode(image_base64))
                tmp_path = f.name

            return tmp_path

        else:
            print("Nu s-a generat imaginea.")
            return None

    except Exception as e:
        print(" Eroare generare imagine")
        return None
    
def generate_speech(text: str):
    try:
        # Fișier temporar pentru salvare
        tmp_path = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name)

        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",  # sau gpt-4o când va fi full
            voice="nova",  # coral, nova, shimmer, alloy...
            input=text,
            instructions="Vorbește clar și plăcut, cu o tonalitate prietenoasă."
        ) as response:
            response.stream_to_file(tmp_path)

        return str(tmp_path)

    except Exception as e:
        print("❌ Eroare generare speech:", e)
        return None