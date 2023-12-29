# RU_TTS for NVDA

RU_TTS for NVDA — это русскоязычный синтезатор речи для программы экранного доступа NVDA, созданный на базе свободного голосового движка [ru_tts](https://github.com/poretsky/ru_tts).
Движок ru_tts является альтернативной реализацией программного синтезатора речи «Фонемафон-5» начала 1990-х годов, и характеризуется компактностью, высокой скоростью отклика и повышенной чёткостью речи.

## Новое в версии 2023.05.08
1. ДОбавлена совместимость с NVDA 2023.1.
2. Основной движок ru_tts обновлён до коммита 86297b1.
3. Словарь произношений Rulex обновлён до коммита bd6249e.
4. Библиотека Sonic обновлена до коммита 0555641.
5. Синтезатор больше не произносит символы круглых скобок при их получении от NVDA.
6. Исходные коды дополнения теперь опубликованы на <https://github.com/kvark128/ru_tts-for-nvda>.

## Новое в версии 2022.04.25
1. Добавлена совместимость с NVDA 2022.1.
2. Основной движок ru_tts обновлён до версии 6.0.3.
3. Словарь произношений Rulex обновлён до версии 3.6.1.
4. Добавлена поддержка чтения символов Unicode из кодового пространства Braille Patterns (символы в диапазоне от U+2800 до U+28FF).
5. Библиотека PCRE2, используемая в драйвере Rulex в качестве POSIX-совместимого средства для работы с регулярными выражениями, обновлена до версии 10.40.

## Новое в версии 2021.12.28
1. Исправлено регулярное выражение для поиска аббревиатур. Теперь аббревиатуры определяются в большем числе случаев.
2. Отдельно стоящие буквы латиницы теперь объявляются по своим названиям, также как и при посимвольном чтении.
3. Реализовано чтение ведущих нулей в числах. Ранее в таких строках как «007» нули никак не сообщались.
4. Исправлено посимвольное чтение при снятом флаге «Использовать посимвольное чтение» в настройках речи NVDA.
5. Реализована обработка символа U+0301 (знак ударения). Синтезатор теперь корректно проставляет ударение в словах с этим символом.
6. Изменена структура файла конфигурации ru_tts.ini. Общие параметры синтезатора перемещены в секцию «Parameters».
Если в NVDA ранее была установлена предыдущая версия ru_tts, то после обновления дополнения, во избежание путаницы с дублированием параметров в ru_tts.ini, настоятельно рекомендуется удалить этот файл, перезагрузить синтезатор и при необходимости повторно отредактировать ru_tts.ini.
7. В файл конфигурации ru_tts.ini добавлена секция «Characters», предназначенная для задания фонетических значений произвольных символов/букв.
8. В файл конфигурации ru_tts.ini добавлена секция «SingleCharacters», предназначенная для задания названий произвольных символов/букв при посимвольном чтении.
9. Реализована возможность Unicode-нормализации входного текста, перед его передачей движку ru_tts. Данная функция настраивается с помощью параметров use_unicode_normalization и unicode_normalization_form в файле конфигурации ru_tts.ini.
10. СУБД Berkeley DB, используемая в библиотеке RuLex, обновлена до версии 18.1.40.
11. В состав дополнения включены лицензии всех сторонних зависимостей.

## Новое в версии 2021.11.14
1. Основной движок ru_tts обновлён до версии 6.0.2.
2. Словарь произношений RuLex обновлён до версии 3.6.0.
3. Библиотека sonic, используемая для функции дополнительного ускорения и регулировки громкости, обновлена до коммита e06dbb9.
4. Сбой загрузки базы данных словаря произношений RuLex, наблюдаемый на некоторых старых машинах, больше не приводит к невозможности использования синтезатора. ru_tts в этом случае корректно загрузится, но флаг «Использовать словарь произношений RuLex», в настройках речи, будет недоступен.
5. Некоторые настройки синтезатора вынесены в конфигурационный файл ru_tts.ini, создаваемый при первой загрузке в пользовательском каталоге настроек NVDA. Для установочной версии это %APPDATA%\nvda.