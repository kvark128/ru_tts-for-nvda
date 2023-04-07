[Parameters]
# Частота дискретизации выходного аудиоустройства. Допустимые значения от 8000 до 16000. По умолчанию 10000
samples_per_sec = integer(min=8000, max=16000, default=10000)

# Пауза после запятой. Допустимые значения от 0 до 750. По умолчанию 100
comma_gap_factor = integer(min=0, max=750, default=100)

# Пауза после точки. Допустимые значения от 0 до 500. По умолчанию 100
dot_gap_factor = integer(min=0, max=500, default=100)

# Пауза после точки с запятой. Допустимые значения от 0 до 600. По умолчанию 100
semicolon_gap_factor = integer(min=0, max=600, default=100)

# Пауза после двоеточия. Допустимые значения от 0 до 600. По умолчанию 100
colon_gap_factor = integer(min=0, max=600, default=100)

# Пауза после вопросительного знака. Допустимые значения от 0 до 375. По умолчанию 100
question_gap_factor = integer(min=0, max=375, default=100)

# Пауза после восклицательного знака. Допустимые значения от 0 до 300. По умолчанию 100
exclamation_gap_factor = integer(min=0, max=300, default=100)

# Интонационная пауза. Допустимые значения от 0 до 1000. По умолчанию 100
intonational_gap_factor = integer(min=0, max=1000, default=100)

# Использовать точку в качестве десятичного разделителя. Допустимые значения True или False. По умолчанию False
dec_sep_point = boolean(default=False)

# Использовать запятую в качестве десятичного разделителя. Допустимые значения True или False. По умолчанию True
dec_sep_comma = boolean(default=True)

# Использовать Unicode-нормализацию читаемого текста. Допустимые значения True или False. По умолчанию False
# Форма нормализации определяется параметром unicode_normalization_form
use_unicode_normalization = boolean(default=False)

# Форма Unicode-нормализации читаемого текста. Учитывается только если параметр use_unicode_normalization имеет значение True
# Допустимые значения: NFC, NFKC, NFD или NFKD. По умолчанию NFC
unicode_normalization_form = string(default=NFC)

[Characters]
j = string(default=дж)
q = string(default=ку)
w = string(default=в)
x = string(default=кс)

[SingleCharacters]
б = string(default=бэ)
в = string(default=вэ)
с = string(default=эс)
к = string(default=ка)
ь = string(default=мягкий знак)
ъ = string(default=твёрдый знак)

a = string(default=эй)
b = string(default=би)
c = string(default=си)
d = string(default=ди)
e = string(default=и)
f = string(default=эф)
g = string(default=джи)
h = string(default=эйчь)
i = string(default=ай)
j = string(default=джей)
k = string(default=кей)
l = string(default=эл)
m = string(default=эм)
n = string(default=эн)
o = string(default=оу)
p = string(default=пи)
q = string(default=къю)
r = string(default=ар)
s = string(default=эс)
t = string(default=ти)
u = string(default=ю)
v = string(default=ви)
w = string(default=даблъю)
x = string(default=экс)
y = string(default=вай)
z = string(default=зэт)
