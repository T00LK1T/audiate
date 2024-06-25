import logging
import os
import time

import speech_recognition as sr
from pydub import AudioSegment


class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def ask_google(self, audio: sr.AudioData, language: str = "ko-KR"):
        """
        구글 음성 인식 API를 사용하여 음성을 텍스트로 변환

        recognize_google은 legacy API이며 패키지에서 지원하지 않을 목적인지 참조가 없음
        https://github.com/Uberi/speech_recognition/blob/75a7f6b83850318e29d6bc60b372ada2558c6343/speech_recognition/recognizers/google.py#L225C5-L225C21
        """
        return self.recognizer.recognize_google(audio, language=language)  # type: ignore

    async def recognize_speech(self, path: str) -> str:
        with sr.AudioFile(path) as source:
            audio = self.recognizer.record(source)
            return await self.ask_google(audio)

    def tokenize_audio(
        self,
        audio: AudioSegment,
        skip_ms: int,
        token_ms: int,
        wait_ms: int,
        padding_ms: int,
    ):
        chunks = []
        for start_ms in range(skip_ms, len(audio), token_ms + wait_ms):
            end_ms = start_ms + token_ms
            # 각 청크의 시작과 끝에 패딩 추가
            padded_chunk = (
                AudioSegment.silent(duration=padding_ms)
                + audio[start_ms:end_ms]
                + AudioSegment.silent(duration=padding_ms)
            )
            chunks.append(padded_chunk)
        return chunks

    async def recognize_padding_speech(self, path: str, remove_temp_files=True) -> str:
        skip_ms = 100
        token_ms = 600
        wait_ms = 100
        padding_ms = 500

        audio = AudioSegment.from_file(path)
        chunks = self.tokenize_audio(audio, skip_ms, token_ms, wait_ms, padding_ms)
        audio_with_pads = AudioSegment.empty()
        for chunk in chunks:
            audio_with_pads += chunk
        ts = time.time()
        filename, ext = path.split(".")
        new_filename = f"{filename}_{ts}.{ext}"
        audio_with_pads.export(new_filename, format=ext)

        result = ""
        with sr.AudioFile(new_filename) as source:
            audio_data = self.recognizer.record(source)
            try:
                result = await self.ask_google(audio_data)
            except sr.UnknownValueError:
                logging.exception(
                    "Google Speech Recognition could not understand audio"
                )
            except sr.RequestError as e:
                logging.exception(
                    "Could not request results "
                    "from Google Speech Recognition service; "
                    "%s",
                    e,
                )
            finally:
                if remove_temp_files:
                    os.remove(new_filename)
        return result

    async def recognize_tokenized_speech(
        self, path: str, remove_temp_files=True
    ) -> str:
        skip_ms = 100
        token_ms = 600
        wait_ms = 100
        padding_ms = 200

        ts = time.time()

        audio = AudioSegment.from_file(path)
        chunks = self.tokenize_audio(audio, skip_ms, token_ms, wait_ms, padding_ms)
        results = []
        for i, chunk in enumerate(chunks):
            chunk.export(f"chunk_{i}_{ts}.wav", format="wav")
            with sr.AudioFile(f"chunk_{i}_{ts}.wav") as source:
                audio_data = self.recognizer.record(source)
                try:
                    result = await self.ask_google(audio_data)
                    results.append(result)
                except sr.UnknownValueError:
                    logging.exception(
                        "Google Speech Recognition could not understand audio"
                    )
                    results.append("")
                except sr.RequestError as e:
                    logging.exception(
                        "Could not request results "
                        "from Google Speech Recognition service;"
                        " %s",
                        e,
                    )
                    results.append("")
                finally:
                    if remove_temp_files:
                        os.remove(f"chunk_{i}_{ts}.wav")
        return "".join(results)
