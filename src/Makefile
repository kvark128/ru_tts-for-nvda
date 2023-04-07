# Makefile for ru_tts for NVDA
#
# Copyright (C) 2023 Alexander Linkov <kvark128@yandex.ru>

CC = gcc
CFLAGS = -Wall -Werror -Wno-unused-result -m32 -O2
RULEX_LIBS = -ldb -lpthread -lpcre2-posix -lpcre2-8
NVDA_ADDON = nvda-addon
LEXICON_DIR = ../external/rulex/data
LEXHOLDER_DIR = ../external/rulex/src
VPATH = ../external/ru_tts/src:../external/sonic:../external/rulex/src

all: ru_tts.nvda-addon

.SILENT: clean
clean:
	rm -f *.o *.a *.exe *.dll *.db $(LEXHOLDER_DIR)/*.exe
	$(MAKE) -s -C $(LEXICON_DIR) clean
	cd $(NVDA_ADDON)/synthDrivers/ru_tts && rm -f *.dll *.db
	rm -f $(NVDA_ADDON)/locale/*/LC_MESSAGES/*.mo
	rm -f *.nvda-addon

%.o: %.c
	$(CC) -c -I../external/sonic $(CFLAGS) $< -o $@

librutts.a: utterance.o transcription.o time_planner.o text2speech.o synth.o speechrate_control.o soundproducer.o sink.o numerics.o male.o intonator.o female.o
	ar rcs $@ $^

lexholder.exe: lexholder.o lexdb.o coder.o
	$(CC) -s $(CFLAGS) -o $@ $^ $(RULEX_LIBS)
	install -p $@ $(LEXHOLDER_DIR)/$@

ru_tts.dll: ru_tts_nvda.o librutts.a sonic.o
	$(CC) -shared -s $(CFLAGS) -o $@ $^

rulex.dll: lexdb.o coder.o
	$(CC) -shared -s $(CFLAGS) -o $@ $^ $(RULEX_LIBS)

rulex.db: lexholder.exe
	$(MAKE) -C $(LEXICON_DIR)
	install -p $(LEXICON_DIR)/lexicon $@

ru_tts.nvda-addon: ru_tts.dll rulex.dll rulex.db
	for dir in $(NVDA_ADDON)/locale/*/LC_MESSAGES; do \
	msgfmt -o $$dir/nvda.mo $$dir/nvda.po; done
	cp $^ $(NVDA_ADDON)/synthDrivers/ru_tts
	cd $(NVDA_ADDON) && 7z a -tzip ../$@ *

synth.o: synth.c synth.h transcription.h soundscript.h ru_tts.h
numerics.o: numerics.c numerics.h transcription.h sink.h synth.h ru_tts.h
transcription.o: transcription.c transcription.h numerics.h sink.h
utterance.o: utterance.c soundscript.h transcription.h
time_planner.o: time_planner.c soundscript.h transcription.h
speechrate_control.o: speechrate_control.c timing.h soundscript.h transcription.h
intonator.o: intonator.c transcription.h soundscript.h modulation.h
soundproducer.o: soundproducer.c sink.h soundscript.h voice.h
sink.o: sink.c sink.h ru_tts.h
male.o: male.c voice.h
female.o: female.c voice.h
text2speech.o: text2speech.c ru_tts.h sink.h transcription.h synth.h timing.h modulation.h
sonic.o: sonic.c sonic.h
lexholder.o: lexholder.c lexdb.h
lexdb.o: lexdb.c lexdb.h coder.h
coder.o: coder.c coder.h
ru_tts_nvda.o: ru_tts_nvda.c ru_tts_nvda.h
