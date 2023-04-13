# Copyright (C) 2021 - 2023 Александр Линьков <kvark128@yandex.ru>
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.

import os.path
import threading
import queue
import re
import unicodedata
from collections import OrderedDict
from ctypes import *

import config
import addonHandler
import globalVars
import nvwave
from configobj import ConfigObj
from configobj.validate import Validator
from speech.commands import IndexCommand, PitchCommand, SpeechCommand
from synthDriverHandler import SynthDriver, VoiceInfo, synthIndexReached, synthDoneSpeaking
from autoSettingsUtils.driverSetting import NumericDriverSetting, BooleanDriverSetting
from logHandler import log

addonHandler.initTranslation()

MODULE_DIR = os.path.dirname(__file__)
RU_TTS_LIB_PATH = os.path.join(MODULE_DIR, "ru_tts.dll")
RULEX_LIB_PATH = os.path.join(MODULE_DIR, "rulex.dll")
RULEX_DB_PATH = os.path.join(MODULE_DIR, "rulex.db")
CONFIG_FILE_PATH = os.path.join(globalVars.appArgs.configPath, "ru_tts.ini")
CONFIG_SPEC_PATH = os.path.join(MODULE_DIR, "config.spec")
RU_TTS_CALLBACK = CFUNCTYPE(c_int, c_void_p, c_size_t, c_void_p)
BRAILLE_DOT_LABELS = ("первая", "вторая", "третья", "четвёртая", "пятая", "шестая", "седьмая", "восьмая")

SINGLE_CHARACTER_TRANSLATION_DICT = {
	# Подавляем произношение круглых скобок, заменяя их на пробелы
	ord('('): ' ',
	ord(')'): ' ',
	# Добавляем поддержку знака ударения
	ord('\u0301'): '+',
}

# Регулярные выражения для коррекции произношения
RE_WORDS = re.compile("[а-яё\u0301]+", re.I)
RE_ABBREVIATIONS = re.compile(r"(?<![а-яёa-z])[bcdfghjklmnpqrstvwxzбвгджзклмнпрстфхцчшщ]{2,}(?![а-яёa-z])", re.I)
RE_LETTER_AFTER_NUMBER = re.compile(r"\d[а-яёa-z]", re.I)
RE_SINGLE_LATIN = re.compile(r"(?<![а-яёa-z])[a-z](?![а-яёa-z])", re.I)
RE_BRAILLE_PATTERNS = re.compile(r"[\u2800-\u28ff]")

# Диапазоны допустимых значений для скорости, высоты и интонации речи
RATE_MIN = 20
RATE_MAX = 250 # движок поддерживает максимальное значение 500, но при значении более 250 наблюдается искажение звука
PITCH_MIN = 50
PITCH_MAX = 300
INTONATION_MIN = 0
INTONATION_MAX = 140

@POINTER
class TTS(Structure): pass

@POINTER
class RULEXDB(Structure): pass

# Ограничения на размер некоторых значений при работе с базой данных rulex
RULEXDB_MAX_KEY_SIZE = 50
RULEXDB_MAX_RECORD_SIZE = 200
RULEXDB_BUFSIZE = 256

# Режимы доступа к базе данных rulex
RULEXDB_SEARCH = 0
RULEXDB_UPDATE = 1
RULEXDB_CREATE = 2

# Коды возврата при работе с базой данных rulex
RULEXDB_SUCCESS = 0
RULEXDB_SPECIAL = 1
RULEXDB_FAILURE = -1
RULEXDB_EMALLOC = -2
RULEXDB_EINVKEY = -3
RULEXDB_EINVREC = -4
RULEXDB_EPARM = -5
RULEXDB_EACCESS = -6

# Управляющие флаги для поля flags в структуре RU_TTS_CONF_T
DEC_SEP_POINT = 1 # Использовать точку в качестве десятичного разделителя
DEC_SEP_COMMA = 2 # Использовать запятую в качестве десятичного разделителя
USE_ALTERNATIVE_VOICE = 4 # Использовать женский голос

class RU_TTS_CONF_T(Structure):
	_fields_ = [
		("speech_rate", c_int),
		("voice_pitch", c_int),
		("intonation", c_int),
		("general_gap_factor", c_int),
		("comma_gap_factor", c_int),
		("dot_gap_factor", c_int),
		("semicolon_gap_factor", c_int),
		("colon_gap_factor", c_int),
		("question_gap_factor", c_int),
		("exclamation_gap_factor", c_int),
		("intonational_gap_factor", c_int),
		("flags", c_int),
	]

# Параметры синтезатора настраиваемые через графический интерфейс
SPEECH_RATE_PARAM = "speech_rate"
VOICE_PITCH_PARAM = "voice_pitch"
INTONATION_PARAM = "intonation"
GENERAL_GAP_FACTOR_PARAM = "general_gap_factor"
FLAGS_PARAM = "flags"

# Возвращаемые значения для функции обратного вызова, обрабатывающей аудиоданные
CALLBACK_CONTINUE_SYNTHESIS = 0
CALLBACK_ABORT_SYNTHESIS = 1

class AudioCallback(object):

	def __init__(self, silence_flag, player):
		self.__silence_flag = silence_flag
		self.__player = player

	def __call__(self, buffer, size, user_data):
		if self.__silence_flag.is_set():
			return CALLBACK_ABORT_SYNTHESIS
		try:
			if size > 0:
				data = string_at(buffer, size*sizeof(c_short))
				self.__player.feed(data)
			if self.__silence_flag.is_set():
				return CALLBACK_ABORT_SYNTHESIS
			return CALLBACK_CONTINUE_SYNTHESIS
		except Exception:
			log.error("ru_tts AudioCallback", exc_info=True)
			return CALLBACK_ABORT_SYNTHESIS

class RulexDict(object):

	def __init__(self, db_path):
		# Загрузка rulex.dll. Драйвера базы данных для словаря произношений
		self.__rulexdb = CDLL(RULEX_LIB_PATH)
		self.__rulexdb.rulexdb_open.argtypes = (c_char_p, c_int)
		self.__rulexdb.rulexdb_open.restype = RULEXDB
		self.__rulexdb.rulexdb_search.argtypes = (RULEXDB, c_char_p, c_char_p, c_int)
		self.__rulexdb.rulexdb_search.restype = c_int
		self.__rulexdb.rulexdb_close.argtypes = (RULEXDB,)

		# Открытие базы данных со словарём произношений и создание буфера в который мы будем получать результаты поиска по этой базе
		# При открытии базы данных драйверу передаётся указатель на строку с путём к файлу. Эта строка используется позже, поэтому нам необходимо защитить ее от сборки мусора
		self.__searchBuf = create_string_buffer(RULEXDB_BUFSIZE)
		self.__db_path = db_path.encode("mbcs")
		self.__db = self.__rulexdb.rulexdb_open(self.__db_path, RULEXDB_SEARCH)
		if not self.__db:
			raise RuntimeError("rulex: failed to open the dictionary database")

	def search(self, match):
		word = match.group()
		key = word.lower().encode("koi8-r", "replace")
		if len(key) <= RULEXDB_MAX_KEY_SIZE:
			if self.__rulexdb.rulexdb_search(self.__db, key, self.__searchBuf, 0) == RULEXDB_SUCCESS:
				return self.__searchBuf.value.decode("koi8-r")
		return word

	def close(self):
		if self.__db:
			self.__rulexdb.rulexdb_close(self.__db)
		try:
			windll.kernel32.FreeLibrary(self.__rulexdb._handle)
		except Exception:
			log.error("rulex: can not unload dll")
		finally:
			self.__rulexdb = None

class SpeakText(object):

	def __init__(self, text, lib, tts, tts_config, silence_flag, index, onIndexReached):
		self.__text = text
		self.__lib = lib
		self.__tts = tts
		self.__config = tts_config
		self.__silence_flag = silence_flag
		self.__index = index
		self.__onIndexReached = onIndexReached

	def __call__(self):
		if self.__silence_flag.is_set():
			return
		text = self.__text.encode("koi8-r", "replace")
		if text:
			self.__lib.tts_speak(self.__tts, byref(self.__config), text)
		if self.__index is None or self.__silence_flag.is_set():
			return
		self.__onIndexReached(self.__index)

class DoneSpeaking(object):

	def __init__(self, player, onIndexReached):
		self.__player = player
		self.__onIndexReached = onIndexReached

	def __call__(self):
		self.__player.idle()
		self.__onIndexReached(None)

class SetParameter(object):

	def __init__(self, conf, param, value):
		self.__config = conf
		self.param = param
		self.value = value

	def __call__(self):
		setattr(self.__config, self.param, self.value)

class TaskThread(threading.Thread):

	def __init__(self, task_queue):
		super().__init__()
		self.__queue = task_queue
		self.daemon = True

	def run(self):
		while True:
			try:
				task = self.__queue.get()
				if task is None:
					break
				task()
			except Exception:
				log.error("ru_tts: error while processing a task", exc_info=True)

class SynthDriver(SynthDriver):
	name = "ru_tts"
	description = "ru_tts"

	supportedSettings = [
		SynthDriver.VoiceSetting(),
		SynthDriver.RateSetting(),
		SynthDriver.RateBoostSetting(),
		SynthDriver.PitchSetting(),
		SynthDriver.VolumeSetting(),
		SynthDriver.InflectionSetting(),
		NumericDriverSetting("gapFactor", _("Pause between phrases"), availableInSettingsRing=True),
	]

	supportedCommands = {IndexCommand, PitchCommand}
	supportedNotifications = {synthIndexReached, synthDoneSpeaking}

	def __init__(self):
		# Первым делом загружаем основной движок синтезатора
		self.__ru_tts_lib = CDLL(RU_TTS_LIB_PATH)
		self.__ru_tts_lib.tts_create.argtypes = (RU_TTS_CALLBACK,)
		self.__ru_tts_lib.tts_create.restype = TTS
		self.__ru_tts_lib.tts_destroy.argtypes = (TTS,)
		self.__ru_tts_lib.tts_speak.argtypes = (TTS, POINTER(RU_TTS_CONF_T), c_char_p)
		self.__ru_tts_lib.tts_setVolume.argtypes = (TTS, c_float)
		self.__ru_tts_lib.tts_setSpeed.argtypes = (TTS, c_float)
		self.__ru_tts_lib.ru_tts_config_init.argtypes = (POINTER(RU_TTS_CONF_T),)

		self.__config = RU_TTS_CONF_T()
		self.__ru_tts_lib.ru_tts_config_init(byref(self.__config))
		self.__user_config = self._getUserConfiguration()

		params = self.__user_config["Parameters"]
		self.__config.comma_gap_factor = params["comma_gap_factor"]
		self.__config.dot_gap_factor = params["dot_gap_factor"]
		self.__config.semicolon_gap_factor = params["semicolon_gap_factor"]
		self.__config.colon_gap_factor = params["colon_gap_factor"]
		self.__config.question_gap_factor = params["question_gap_factor"]
		self.__config.exclamation_gap_factor = params["exclamation_gap_factor"]
		self.__config.intonational_gap_factor = params["intonational_gap_factor"]
		self.__config.flags = 0

		if params["dec_sep_point"]:
			self.__config.flags |= DEC_SEP_POINT

		if params["dec_sep_comma"]:
			self.__config.flags |= DEC_SEP_COMMA

		self.__normalizationForm = None
		if params["use_unicode_normalization"]:
			validForms = ("NFC", "NFKC", "NFD", "NFKD")
			form = params["unicode_normalization_form"]
			if form in validForms:
				self.__normalizationForm = form

		try:
			self.__rulex_dict = RulexDict(RULEX_DB_PATH)
		except Exception:
			self.__rulex_dict = None
			log.warning("rulex not available", exc_info=True)
		else:
			self.__rulexSetting = BooleanDriverSetting("useRulex", _("Use RuLex pronunciation dictionary"), availableInSettingsRing=True)
			self.supportedSettings.append(self.__rulexSetting)

		self.__silence_flag = threading.Event()
		self.__player = nvwave.WavePlayer(channels=1, samplesPerSec=params["samples_per_sec"], bitsPerSample=16, outputDevice=config.conf["speech"]["outputDevice"])
		self.__audio_callback = AudioCallback(self.__silence_flag, self.__player)

		self.__c_audio_callback = RU_TTS_CALLBACK(self.__audio_callback)
		self.__tts = self.__ru_tts_lib.tts_create(self.__c_audio_callback)
		if not self.__tts:
			raise RuntimeError("ru_tts: failed to create a TTS instance")

		self.__speechFlags = self.__config.flags
		self.__rate = self._paramToPercent(self.__config.speech_rate, RATE_MIN, RATE_MAX)
		self.__rateBoost = False
		self.__pitch = self._paramToPercent(self.__config.voice_pitch, PITCH_MIN, PITCH_MAX)
		self.__volume = 50
		self.__ru_tts_lib.tts_setVolume(self.__tts, self.__volume/100)
		self.__inflection = self._paramToPercent(self.__config.intonation, INTONATION_MIN, INTONATION_MAX)
		self.__gap_factor_max = self._maxGapRange(self.__config.speech_rate)
		self.__gapFactor = self._paramToPercent(self.__config.general_gap_factor, 0, self.__gap_factor_max)
		self.__useRulex = False

		self.__task_queue = queue.Queue()
		self.__task_thread = TaskThread(self.__task_queue)
		self.__task_thread.start()

	@classmethod
	def check(cls):
		return True

	def terminate(self):
		self.cancel()
		self.__task_queue.put(None)
		self.__task_thread.join()
		self.__player.close()
		if self.__rulex_dict is not None:
			self.supportedSettings.remove(self.__rulexSetting)
			self.__rulex_dict.close()
			self.__rulex_dict = None
		self.__config = None
		self.__ru_tts_lib.tts_destroy(self.__tts)
		self.__tts = None
		# Предотвращаем образование циклических ссылок
		self.__audio_callback = None
		self.__c_audio_callback = None
		# Пробуем выгрузить основной движок синтезатора
		try:
			windll.kernel32.FreeLibrary(self.__ru_tts_lib._handle)
		except Exception:
			log.error("ru_tts: can not unload dll")
		finally:
			self.__ru_tts_lib = None

	def _getUserConfiguration(self):
		with open(CONFIG_SPEC_PATH, encoding="utf-8") as spec:
			conf = ConfigObj(infile=CONFIG_FILE_PATH, configspec=spec, encoding="utf-8", default_encoding="utf-8")
		val = Validator()
		conf.validate(val, copy=True)
		if not globalVars.appArgs.secure:
			try:
				conf.write()
			except OSError:
				log.error("ru_tts: failed to write config file", exc_info=True)
		return conf

	def _setParameter(self, param, value):
		task = SetParameter(self.__config, param, value)
		self.__task_queue.put(task)

	def speak(self, speechSequence):
		textList = []
		for item in speechSequence:
			if isinstance(item, str):
				textList.append(item)
			elif isinstance(item, IndexCommand):
				self.do_speak(textList, item.index)
				textList = []
			elif isinstance(item, PitchCommand):
				self.do_speak(textList)
				textList = []
				pitch = self._percentToParam(item.newValue, PITCH_MIN, PITCH_MAX)
				self._setParameter(VOICE_PITCH_PARAM, pitch)
			elif isinstance(item, SpeechCommand):
				log.debugWarning(f"Unsupported speech command: {item}")
			else:
				log.error(f"Unknown speech: {item}")
		self.do_speak(textList)
		self.__task_queue.put(DoneSpeaking(self.__player, self._onIndexReached))

	def do_speak(self, textList, index=None):
		text = "".join(textList).strip()
		if self.__normalizationForm is not None:
			text = unicodedata.normalize(self.__normalizationForm, text)
		if len(text) == 1:
			text = self.__user_config["SingleCharacters"].get(text.lower(), text)
		else:
			text = RE_SINGLE_LATIN.sub(self._singleLatinSearch, text)
			text = RE_ABBREVIATIONS.sub(self._abbreviationSearch, text)
			text = RE_LETTER_AFTER_NUMBER.sub(self._letterAfterNumberSearch, text)
			text = "".join([self.__user_config["Characters"].get(ch.lower(), ch) for ch in text])
		if self.__useRulex and (self.__rulex_dict is not None):
			text = RE_WORDS.sub(self.__rulex_dict.search, text)
		text = text.translate(SINGLE_CHARACTER_TRANSLATION_DICT)
		text = RE_BRAILLE_PATTERNS.sub(self._brailleDotsSearch, text)
		task = SpeakText(text, self.__ru_tts_lib, self.__tts, self.__config, self.__silence_flag, index, self._onIndexReached)
		self.__task_queue.put(task)

	def pause(self, switch):
		self.__player.pause(switch)

	def cancel(self):
		tasks = []
		try:
			while True:
				task = self.__task_queue.get_nowait()
				if not isinstance(task, SpeakText):
					tasks.append(task)
		except queue.Empty:
			pass
		for task in tasks:
			self.__task_queue.put(task)
		self.__silence_flag.set()
		self.__task_queue.put(self.__silence_flag.clear)
		self.__player.stop()

	def _singleLatinSearch(self, match):
		ch = match.group().lower()
		return self.__user_config["SingleCharacters"].get(ch, ch)

	def _abbreviationSearch(self, match):
		word = match.group().lower()
		return " ".join([self.__user_config["SingleCharacters"].get(ch, ch) for ch in word])

	def _letterAfterNumberSearch(self, match):
		return " ".join(match.group())

	def _brailleDotsSearch(self, match):
		ch = match.group()
		dotLabels = []
		for offset, label in enumerate(BRAILLE_DOT_LABELS):
			if ord(ch) >> offset & 1:
				dotLabels.append(label)
		if len(dotLabels) == 0:
			return " брайлевский пробел "
		elif len(dotLabels) == 8:
			return " брайлевское восьмиточие "
		else:
			dotLabels.append("брайлевские точки" if len(dotLabels) > 1 else "брайлевская точка")
			return f" {' '.join(dotLabels)} "

	def _onIndexReached(self, index):
		if index is not None:
			synthIndexReached.notify(synth=self, index=index)
		else:
			synthDoneSpeaking.notify(synth=self)

	def _maxGapRange(self, rate):
		return 125 * rate // RATE_MIN

	def _get_language(self):
		return "ru"

	def _get_rate(self):
		return self.__rate

	def _set_rate(self, value):
		self.__rate = value
		rate = self._percentToParam(self.__rate, RATE_MIN, RATE_MAX)
		self._setParameter(SPEECH_RATE_PARAM, rate)
		# Коэффициент паузы зависит от скорости речи. Необходимо вычислить его заново
		self.__gap_factor_max = self._maxGapRange(rate)
		gap_factor = self._percentToParam(self.__gapFactor, 0, self.__gap_factor_max)
		self._setParameter(GENERAL_GAP_FACTOR_PARAM, gap_factor)

	def _get_pitch(self):
		return self.__pitch

	def _set_pitch(self, value):
		self.__pitch = value
		pitch = self._percentToParam(self.__pitch, PITCH_MIN, PITCH_MAX)
		self._setParameter(VOICE_PITCH_PARAM, pitch)

	def _get_volume(self):
		return self.__volume

	def _set_volume(self, volume):
		self.__volume = volume
		task = lambda: self.__ru_tts_lib.tts_setVolume(self.__tts, volume/100)
		self.__task_queue.put(task)

	def _getAvailableVoices(self):
		voices = OrderedDict()
		for id, displayName in enumerate((_("Male"), _("Female"))):
			id = str(id)
			voices[id] = VoiceInfo(id, displayName, "ru")
		return voices

	def _get_voice(self):
		return str((self.__speechFlags & USE_ALTERNATIVE_VOICE) >> 2)

	def _set_voice(self, voice):
		if voice in self.availableVoices:
			if (int(voice) << 2) == USE_ALTERNATIVE_VOICE:
				self.__speechFlags |= USE_ALTERNATIVE_VOICE
			else:
				self.__speechFlags &= ~USE_ALTERNATIVE_VOICE
			self._setParameter(FLAGS_PARAM, self.__speechFlags)

	def _get_rateBoost(self):
		return self.__rateBoost

	def _set_rateBoost(self, enable):
		if enable != self.__rateBoost:
			self.__rateBoost = enable
			speed = 2.0 if self.__rateBoost else 1.0
			task = lambda: self.__ru_tts_lib.tts_setSpeed(self.__tts, speed)
			self.__task_queue.put(task)

	def _get_gapFactor(self):
		return self.__gapFactor

	def _set_gapFactor(self, value):
		self.__gapFactor = value
		gap_factor = self._percentToParam(self.__gapFactor, 0, self.__gap_factor_max)
		self._setParameter(GENERAL_GAP_FACTOR_PARAM, gap_factor)

	def _get_inflection(self):
		return self.__inflection

	def _set_inflection(self, value):
		self.__inflection = value
		intonation = self._percentToParam(self.__inflection, INTONATION_MIN, INTONATION_MAX)
		self._setParameter(INTONATION_PARAM, intonation)

	def _get_useRulex(self):
		return self.__useRulex

	def _set_useRulex(self, value):
		self.__useRulex = value
