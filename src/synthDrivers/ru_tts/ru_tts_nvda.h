// Copyright (C) 2021 - 2023 Александр Линьков <kvark128@yandex.ru>
// Этот файл распространяется под лицензией MIT

#include <sonic.h>
#include <ru_tts.h>

typedef struct {
	sonicStream stream;
	void *buffer;
	ru_tts_callback consumer;
} TTS_t;

// tts_create принимает функцию обратного вызова для аудиоданных, инициализирует и возвращает указатель на экземпляр TTS.
// Если инициализация не удалась, возвращается NULL.
// Все дальнейшие операции по синтезу речи выполняются при помощи этого указателя.
// По окончании работы, экземпляр TTS необходимо уничтожить, вызвав tts_destroy
RUTTS_EXPORT TTS_t* tts_create(ru_tts_callback wave_consumer);

// tts_destroy уничтожает экземпляр TTS, освобождая всю выделенную для него память.
// После вызова tts_destroy, указатель на экземпляр TTS становится недействительным и больше не должен никак использоваться.
RUTTS_EXPORT void tts_destroy(TTS_t *tts);

// tts_speak принимает указатель на экземпляр TTS, указатель на структуру с конфигурацией синтезируемой речи, и текст в кодировке KOI8-R, который далее и произносится.
// Все синтезированные аудиоданные передаются порциями в функцию обратного вызова, установленную при создании экземпляра TTS.
RUTTS_EXPORT void tts_speak(const TTS_t *tts, const ru_tts_conf_t *config, const char *text);

// tts_setVolume задаёт громкость синтезируемых аудиоданных для экземпляра TTS. Значение громкости по умолчанию 1.0.
RUTTS_EXPORT void tts_setVolume(const TTS_t *tts, float volume);

// tts_setSpeed задаёт скорость синтезируемых аудиоданных для экземпляра TTS. Значение скорости по умолчанию 1.0.
RUTTS_EXPORT void tts_setSpeed(const TTS_t *tts, float speed);
