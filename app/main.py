import asyncio
import pathlib

from speech_recognizer import SpeechRecognizer


async def main():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
    SOUND_DIR = BASE_DIR / "sounds"

    result_map = {}

    def get_file_list(dir_path: pathlib.Path):
        for path in dir_path.iterdir():
            if path.is_file():
                yield path

    async def get_result(recognizer: SpeechRecognizer, path: str):
        text = await recognizer.recognize_padding_speech(path, remove_temp_files=True)
        result = text.replace(" ", "")
        return result

    async with SpeechRecognizer() as recognizer:
        for path in get_file_list(SOUND_DIR):
            result = await get_result(recognizer, str(path))
            result_map[path.name] = result
            print(f"{path.name}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
