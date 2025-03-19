import pyttsx3

def list_voices():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for idx, voice in enumerate(voices):
        if voice.languages == ['en_US']:
            print(f"Voice {idx}:")
            print(f"  ID: {voice.id}")
            print(f"  Name: {voice.name}")
            print(f"  Languages: {voice.languages}")
            print(f"  Gender: {voice.gender}")
            print(f"  Age: {voice.age}")
    engine.stop()

def speak_text_with_voice(text: str, voice_index: int = 0, rate: int = 100):
    engine = pyttsx3.init()
    default_rate = engine.getProperty('rate')
    voices = engine.getProperty('voices')
    if voice_index < len(voices):
        engine.setProperty('voice', voices[voice_index].id)
        engine.setProperty('rate', rate)
    else:
        print("Invalid voice index. Using default.")
    engine.say(text)
    engine.runAndWait()

# List all voices so you know which one you want
list_voices()

# Example: Speak text using the voice at index 1
speak_text_with_voice("Hello, this is a test using voice index 1.", voice_index=103)
