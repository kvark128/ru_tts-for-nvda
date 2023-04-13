// Copyright (C) 2021 - 2023 Александр Линьков <kvark128@yandex.ru>
// Этот файл распространяется под лицензией MIT

#include <stdlib.h>

#include <sonic.h>
#include <ru_tts.h>
#include "ru_tts_nvda.h"

#define SUCCESS 0
#define FAILURE 1

#define WAVE_SIZE 4096
#define SAMPLE_RATE 10000
#define NUM_CHANNELS 1

int writeToConsumer(const TTS_t *tts, const int minSamples) {
	int numSamples = sonicSamplesAvailable(tts->stream);
	while (numSamples >= minSamples) {
		int n = sonicReadShortFromStream(tts->stream, tts->buffer, WAVE_SIZE);
		if (tts->consumer(tts->buffer, n, NULL)) {
			// Пользователь прервал синтез. Необходимо сбросить внутренние буферы sonic
			while (sonicReadShortFromStream(tts->stream, tts->buffer, WAVE_SIZE));
			return FAILURE;
		}
		numSamples -= n;
	}
	return SUCCESS;
}

int audio_callback(void *buffer, size_t size, void *user_data) {
	signed char *samples = (signed char*) buffer;
	TTS_t *tts = (TTS_t*) user_data;
	for (int i = 0; i < size; i++) {
		// Sonic не поддерживает аудиоданные в форме signed char. Преобразуем signed char в unsigned char
		samples[i] ^= 0x80;
	}
	if (sonicWriteUnsignedCharToStream(tts->stream, buffer, size) == 0) {
		return FAILURE;
	}
	return writeToConsumer(tts, WAVE_SIZE);
}

TTS_t* tts_create(ru_tts_callback wave_consumer) {
	if (wave_consumer == NULL) {
		return NULL;
	}
	sonicStream stream = sonicCreateStream(SAMPLE_RATE, NUM_CHANNELS);
	if (stream == NULL) {
		return NULL;
	}
	// Буфер для short-сэмплов
	void *buffer = malloc(WAVE_SIZE * sizeof(short));
	if (buffer == NULL) {
		sonicDestroyStream(stream);
		return NULL;
	}
	TTS_t *tts = malloc(sizeof(TTS_t));
	if (tts == NULL) {
		sonicDestroyStream(stream);
		free(buffer);
		return NULL;
	}
	tts->stream = stream;
	tts->buffer = buffer;
	tts->consumer = wave_consumer;
	return tts;
}

void tts_destroy(TTS_t *tts) {
	if (tts == NULL) {
		return;
	}
	if (tts->stream != NULL) {
		sonicDestroyStream(tts->stream);
		tts->stream = NULL;
	}
	if (tts->buffer != NULL) {
		free(tts->buffer);
		tts->buffer = NULL;
	}
	tts->consumer = NULL;
	free(tts);
}

void tts_speak(const TTS_t *tts, const ru_tts_conf_t *config, const char *text) {
	ru_tts_transfer(config, text, tts->buffer, WAVE_SIZE, audio_callback, (void*)tts);
	sonicFlushStream(tts->stream);
	writeToConsumer(tts, 1);
}

void tts_setVolume(const TTS_t *tts, float volume) {
	sonicSetVolume(tts->stream, volume);
}

void tts_setSpeed(const TTS_t *tts, float speed) {
	sonicSetSpeed(tts->stream, speed);
}
