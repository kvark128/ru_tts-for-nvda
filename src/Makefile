# Makefile for ru_tts for NVDA
#
# Copyright (C) 2023 Alexander Linkov <kvark128@yandex.ru>

CC = gcc
CFLAGS = -Wall -Werror -Wno-unused-result -m32 -O2 -DPCRE2_STATIC
RULEX_LIBS = -ldb -lpthread -lpcre2-posix -lpcre2-8
RU_TTS_OBJS = utterance.o transcription.o time_planner.o text2speech.o synth.o speechrate_control.o soundproducer.o sink.o numerics.o male.o intonator.o female.o
PO_FILES = $(wildcard locale/*/LC_MESSAGES/nvda.po)
MO_FILES = $(addsuffix .mo, $(basename $(PO_FILES)))
MANIFESTS = manifest.ini $(wildcard locale/*/manifest.ini)
SYNTH_DIR = synthDrivers/ru_tts
PY_FILES = $(wildcard $(SYNTH_DIR)/*.py)
LICENSES = $(wildcard $(SYNTH_DIR)/LICENSES/*.txt) $(SYNTH_DIR)/COPYING.txt
EXT_DIR = ../external
LEXICON_DIR = $(EXT_DIR)/rulex/data
LEXHOLDER_DIR = $(EXT_DIR)/rulex/src
VPATH = $(EXT_DIR)/ru_tts/src $(EXT_DIR)/sonic $(EXT_DIR)/rulex/src $(SYNTH_DIR)

all: ru_tts.nvda-addon

pot: ru_tts.pot

.SILENT: clean
clean:
	rm -f *.o *.nvda-addon *.pot
	$(MAKE) -s -C $(LEXICON_DIR) clean
	cd $(LEXHOLDER_DIR) && rm -f *.exe
	cd $(SYNTH_DIR) && rm -f *.dll *.db
	rm -f $(MO_FILES)

%.o: %.c
	$(CC) -c -I$(EXT_DIR)/ru_tts/src -I$(EXT_DIR)/sonic $(CFLAGS) -o $@ $<

%.mo: %.po
	msgfmt -o $@ $<

ru_tts.pot: $(PY_FILES)
	xgettext --package-name ru_tts -o $@ $^

lexholder.exe: lexholder.o lexdb.o coder.o
	$(CC) -s $(CFLAGS) -o $(LEXHOLDER_DIR)/$@ $^ $(RULEX_LIBS)

$(SYNTH_DIR)/ru_tts.dll: ru_tts_nvda.o sonic.o $(RU_TTS_OBJS)
	$(CC) -shared -s $(CFLAGS) -o $@ $^

$(SYNTH_DIR)/rulex.dll: lexdb.o coder.o
	$(CC) -shared -s $(CFLAGS) -o $@ $^ $(RULEX_LIBS)

$(SYNTH_DIR)/rulex.db: lexholder.exe
	$(MAKE) -C $(LEXICON_DIR)
	install -p $(LEXICON_DIR)/lexicon $@

ru_tts.nvda-addon: ru_tts.dll rulex.dll rulex.db config.spec $(MANIFESTS) $(PY_FILES) $(PO_FILES) $(MO_FILES) $(LICENSES)
	7z a -tzip -mx=7 $@ $^

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
