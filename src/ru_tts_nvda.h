// Copyright (C) 2021 - 2023 Alexander Linkov <kvark128@yandex.ru>
// This file is distributed under the MIT license

#include <sonic.h>
#include <ru_tts.h>

typedef struct {
	sonicStream stream;
	void *buffer;
	ru_tts_callback consumer;
} TTS_t;

// tts_create receives a callback function for audio data, initializes and returns a TTS instance. If initialization fails, NULL is returned
// All other operations are performed through this instance
// At the end of the work, the TTS instance must be destroyed by calling tts_destroy
TTS_t* tts_create(ru_tts_callback wave_consumer);

// tts_destroy destroys the TTS instance, freeing all memory allocated to it
// After calling tts_destroy, the pointer to the TTS instance becomes invalid and can no longer be used
void tts_destroy(TTS_t *tts);

// tts_speak gets the TTS instance, TTS config, and KOI8-R encoded text, which is then spoken
// All synthesized audio data is passed in chunks to the callback function set when the TTS instance was created
void tts_speak(const TTS_t *tts, const ru_tts_conf_t *config, const char *text);

// tts_setVolume sets the volume of the synthesized audio data for TTS instance. The default volume value is 1.0
void tts_setVolume(const TTS_t *tts, float volume);

// tts_setSpeed sets the speed of the synthesized audio data for TTS instance. The default speed value is 1.0
void tts_setSpeed(const TTS_t *tts, float speed);
