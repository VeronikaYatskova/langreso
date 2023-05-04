# Подключение модулей

# Анотации типов: Any
from typing import Any, Iterable

# Морфологический анализ слов
import pymorphy2

# nltk: Natural language toolkit
import nltk
from nltk.parse.recursivedescent import RecursiveDescentParser
from nltk.grammar import CFG
from nltk.tree import *
from nltk.tree.prettyprinter import TreePrettyPrinter
import spacy
from spacy import displacy

# Словарь естественного языка
from wiki_ru_wordnet import WikiWordnet

# API
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Работа с базой данных tinydb
from pydantic import BaseModel
from tinydb import TinyDB, Query

# Иное вспомогательное
import re                           # regex
from collections import Counter     # dict[Any, int], где ключ - объект, значение - колличество появлений объекта
import time                         # Для time.time (использования текущего времени)
import pathlib                      # Для работы с путями
import svgling                      # Работа с svg и png 
# import cairosvg
from cairosvg import svg2png


# Инциализация API
app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание объектов анализаторов
morph = pymorphy2.MorphAnalyzer()
nlp = spacy.load("ru_core_news_sm")

# Создание базы данных
db = TinyDB('./db.json')
check = Query()



# Утилита
# Функиця для экстракиця слов из строки или списка строк
# использует регулярные выражения
def get_words(lines: list[str] | str, is_lines_list: bool = True) -> list[str]:
    
    if is_lines_list:
        # Cлучай кодга `lines` - список строк
        lines: list[str]
    
        # Испольвания этой же утилиты для экстракции слов из каждой строки отдельно
        # и возврат всех результатов в одном списке
        words = []
        for line in lines:
            line_words = get_words(line, False)
            words.extend(line_words)
        return words
    
    else:
        # Cлучай кодга `lines` - одна строка
        lines: str
        
        # Нахождение слов с помощью регулярного выражения
        words = re.findall(r'[А-яЁё][А-яЁё\-]*', lines)
        # Приведение всех символов во всех словах в нижний регистр
        words_lower = [word.lower() for word in words]
        return words_lower


# Утилита
# Функция для проведения морфологического анализа новых слов
# и обновления базы данных новыми появлениями известных слов
def parse_words(words: list[Any] | dict[Any, int] | Counter, is_words_dict: bool = True) -> list[dict[str, Any]]:
    
    parsed_words = []
    
    if is_words_dict:
        
        # Cлучай кодга `words` - Counter или словарь
        words: dict[Any, int]
        
        # Для каждого найденого слова
        for word in words.keys():
            
            # Если слово уже есть в базе данных
            if db.search(check.word == word):
                # Изменить кол-во появлений слова в базе данных
                db.update({'amount': words[word]}, check.word == word)
                # Добавить инфорамацию о данном слове в вывод
                parsed_words.append(db.search(check.word == word)[0])
            
            # Иначе (если слово новое для базы данных)
            else:
                # Провести морфологический анализ и выбрать первый вариант анализа
                p_word = morph.parse(word)[0].tag
                # Добавит информацию о граммемах в вывод
                parsed_words.append({'word': word, 'amount': words[word],'POS': p_word.POS, 'animacy': p_word.animacy, 'case': p_word.case, 'gender': p_word.gender, 'mood': p_word.mood,
                                'number': p_word.number, 'person': p_word.person, 'tense': p_word.tense, 'transitivity': p_word.transitivity, 'voice': p_word.voice})
    
    else:
        
        # Cлучай кодга `words` - список
        words : list
        
        # Для каждого найденого слова
        for word in words:
            # Если слово уже есть в базе данных
            if db.search(check.word == word):
                # Добавить инфорамацию о данном слове в вывод
                parsed_words.append(db.search(check.word == word)[0])
            
            # Иначе
            else:
                # Провести морфологический анализ и выбрать первый вариант анализа
                p_word = morph.parse(word)[0].tag
                # Добавит информацию о граммемах в вывод
                parsed_words.append({'word': word, 'amount': 1,'POS': p_word.POS, 'animacy': p_word.animacy, 'case': p_word.case, 'gender': p_word.gender, 'mood': p_word.mood,
                                'number': p_word.number, 'person': p_word.person, 'tense': p_word.tense, 'transitivity': p_word.transitivity, 'voice': p_word.voice})
    return parsed_words


# Утилита
# Функция приведеня слов к норамальной форме  
def to_normal(words: list[str]) -> list[str]:
    
    normal_words = []
    
    # Для каждого слова
    for word in words:
        # Найти нормальную форму
        n_word = morph.parse(word)[0].normal_form
        # Добавит в вывод
        normal_words.append(n_word)
    
    return normal_words

# Утилита
# Функция перевода дерева в картинку svg 
def tree2svg(t):
    img = svgling.draw_tree(t)
    svg_data = img.get_svg()
    return svg_data


# Класс слова для работы с API
class Word(BaseModel):
    word: str										# Cлово
    amount: int										# Кол-во 
    POS: str | None = None							# Часть речи
    animacy: str | None = None						# Одушевлённость
    case: str | None = None							# Падеж
    gender: str | None = None						# Род
    mood: str | None = None							# Наклонение
    number: str | None = None						# Число
    person: str | None = None						# Лицо
    tense: str | None = None						# Время
    transitivity: str | None = None					# Переходность
    voice: str | None = None						# Залог

# Класс текста для работы с API
class Text(BaseModel):
    text: str


# Класс. Структура из 2 слов.
class TwoWords(BaseModel):
    word_1: str
    word_2: str

# Часть API
# Приняте ввода из файла
@app.get('/file/get')
def get_words_from_file(file_path: str):
    
    try:
        # Открытие и чтение файла
        f = open(file_path, 'r')
        lines = f.readlines()
        f.close()
        
        # Экстракция слов
        words = get_words(lines, True)
        word_counts = Counter(words)
        print(word_counts)
        
        # Аналз слов
        parsed_words = parse_words(word_counts, True)
    
    # Ответ с ошибкой
    except FileNotFoundError:
        return {'msg': 'File not found'}
    
    except IsADirectoryError:
        return {'msg': 'File expected, directory given'}
    
    # Ответ с анализом слов
    return {'file': file_path, 'text': lines, 'words': parsed_words}


# Часть API
# Приняте ввода строкой
@app.post('/text/post')
def get_words_from_text(text: Text):
    
    # Экстракция слов
    words = get_words(text.text, False)
    word_counts = Counter(words)
    
    # Аналз слов
    parsed_words = parse_words(word_counts, True)
    
    # Ответ с анализом слов
    return {'text': text.text, 'words': parsed_words}


# Часть API
# Вывод базы даннх
@app.get('/db/get')
def get_all_from_db():
    # Ответ
    return {'db': db.all()}

# Часть API
# Добавить слова в базу данных
@app.post('/db/post')
def save_and_update_db(words: list[Word]):
    
    # Для каждого слова
    for word in words:
        
        # Если слово существует: обновить существующее слово в базе данных
        # Иначе: добавить новое слово в базу данных
        if db.search(check.word == word.word):
            db.update({'amount': word.amount,'POS': word.POS, 'animacy': word.animacy, 'case': word.case, 'gender': word.gender, 'mood': word.mood,
                              'number': word.number, 'person': word.person, 'tense': word.tense, 'transitivity': word.transitivity, 'voice': word.voice}, check.word == word.word)
        else: 
            db.insert({'word': word.word, 'amount': word.amount,'POS': word.POS, 'animacy': word.animacy, 'case': word.case, 'gender': word.gender, 'mood': word.mood,
                              'number': word.number, 'person': word.person, 'tense': word.tense, 'transitivity': word.transitivity, 'voice': word.voice})
    
    # Ответ
    return {'msg': 'db is updated'}

# Часть API
# Удаление слова из базы данных
@app.delete('/db/word/del')
def delete_word(word: str):
    # Если слово есть
    if db.search(check.word == word):
        # Удалить и ответить с опевещением удаления
        db.remove(check.word == word)
        return {'msg': 'word has been deleted'}
    # Иначе (если слова нет)
    else:
        # Ответить с оповещением неизвестного слова
        return {'msg': 'word does not exist'}

# Часть API
# Вывод базы даннх
@app.delete('/db/del')
def clear_db():
    db.truncate()
    return {'msg': 'db is clear'}

# Часть API
# Запись дерева предложения в файл в вормате svg
@app.post('/sentence/post')
def scheme_from_sentences(sentences: list[Text]):
    
    paths = []
    
    for sentence in sentences:
        
        # Создание svg
        doc = nlp(sentence.text)
        svg = displacy.render(doc, style="dep", jupyter=False)
        
        # Нахождение пути к файлу
        file_name = '_'.join([doc[i].text for i in range(min(len(doc), 4)) if not doc[i].is_punct]) + ".svg"
        output_path = pathlib.Path("./images/" + file_name)
        paths.append(output_path)
        
        # Запись в файл (Созранение файла на диске)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(svg)
    
    return {'msg': 'svg are created', 'files': paths}


# Часть API
# Построение дерева предложения
@app.post('/sentence/post_tree')
def tree_from_sentences(sentences: list[Text]):
    
    answer = []
    
    # Для каждого предложения
    for sentence in sentences:

        # Проанализировать слова предложения морфологически
        words = get_words(sentence.text, False)
        parsed_words = parse_words(words, False)
        
        # Cоздать базовую КС граматику текстового дерева предложения
        pre_grammar = """S -> NP VP | VP NP | VP PP | NP | VP \n
        PP -> PREP NP | PREP NUM \n
        CP -> CONJ NP | CONJ VP | CONJ AP | CONJ PRP | CONJ NUM \n
        NP -> N | NPR | NPR NP | NUM NP | AP NP | N NP | N PP | PRP NP | N CP | ADV NP \n 
        VP -> V | V INT | V PP | V NP | PP VP | V ADV | V ADJ | V PRT | ADV VP | V NPR | V GRN | GRN VP | CP VP | V CP \n
        AP -> ADJ | NPR AP | ADV ADJ | ADJ AP | ADJ CP \n
        PRP -> PRT | NPR PRP | GRN PRT | PRT PRP | PRT CP \n
        """
        
        # Для каждого слова в предложении:
        # добавить слово в граматику с нетерминалом его части речи
        for word in parsed_words:
            if word['POS'] == "NOUN":
                x = """N -> \'""" + word["word"] + '\'\n' # имя существительное
                pre_grammar = pre_grammar + x
            elif word['POS'] == "VERB" or word['POS'] == "INFN":
                x = """V -> \'""" + word["word"] + '\'\n' # глагол
                pre_grammar = pre_grammar + x
            elif word['POS'] == "ADJF" or word['POS'] == "ADJS":
                x = """ADJ -> \'""" + word["word"] + '\'\n' # имя прилагательное
                pre_grammar = pre_grammar + x
            elif word['POS'] == "ADVB" or word['POS'] == "COMP" or word['POS'] == "PRED":
                x = """ADV -> \'""" + word["word"] + '\'\n' # наречие
                pre_grammar = pre_grammar + x
            elif word['POS'] == "PRTF" or word['POS'] == "PRTS":
                x = """PRT -> \'""" + word["word"] + '\'\n' # причастие
                pre_grammar = pre_grammar + x
            elif word['POS'] == "GRND":
                x = """GRN -> \'""" + word["word"] + '\'\n' # деепричастие
                pre_grammar = pre_grammar + x
            elif word['POS'] == "NUMR":
                x = """NUM -> \'""" + word["word"] + '\'\n' # числительное
                pre_grammar = pre_grammar + x
            elif word['POS'] == "CONJ":
                x = """CONJ -> \'""" + word["word"] + '\'\n' # союз
                pre_grammar = pre_grammar + x
            elif word['POS'] == "PREP":
                x = """PREP -> \'""" + word["word"] + '\'\n' # предлог
                pre_grammar = pre_grammar + x
            elif word['POS'] == "NPRO":
                x = """NPR -> \'""" + word["word"] + '\'\n' # местоимение
                pre_grammar = pre_grammar + x 
            elif word['POS'] == "PRCL" or word['POS'] == "INTJ":
                x = """INT -> \'""" + word["word"] + '\'\n' # частица и междометие
                pre_grammar = pre_grammar + x       
        
        # Cоздать объект граматики из описывающей строки
        grammar = CFG.fromstring(pre_grammar)

        # Создать рекурсивный парсер по граматике
        rd = RecursiveDescentParser(grammar)
        
        pre_answer = []
        count = 0
        
        # Создать деревья с помощью рекурсивного парсера
        for t in rd.parse(words):
            
            # Для первых трёх деревьев
            if count < 3:
                
                # Сохранить svg дерева
                name = 'images/' + '_'.join(words[i] for i in range(min(len(words), 4))) + '_' + str(count) + '.png'
                sv = tree2svg(t)
                svg2png(sv.tostring(), write_to=name)
                
                # Добавить дерево в текстовом формате и путь к svg в ответ
                dict_1 = {}
                dict_1['str'] = str(t)
                dict_1['tree'] = TreePrettyPrinter(t).text()
                dict_1['path'] = name
                pre_answer.append(dict_1)

                count = count + 1
                print(TreePrettyPrinter(t).text())
        
        answer.append(pre_answer)
    
    
    return {'msg': answer}

# Часть API
# 
@app.post('/sentence/post_subtree')
def subtree_from_tree(tree: list[Text]):

    answer = []

    for tr in tree:

        words = get_words(tr.text, type=False)
        dict_1 = {}
        dict_1['str'] = tr.text
        _tr = Tree.fromstring(tr.text)
        dict_1['tree'] = TreePrettyPrinter(_tr).text()
        sv = tree2svg(_tr)
        name = 'images/' + str(time.time())+ '.png'
        svg2png(sv.tostring(), write_to=name)
        dict_1['path'] = name
        answer.append(dict_1)
    
    return {'msg': answer}

# Часть API
# Нахождение отношений между словами в предложениях
@app.post('/words/inform')
def get_new_info_about_words(sentences: list[Text]):

    # Cоздать объект словоря естественного языка
    wikiwordnet = WikiWordnet()

    graph = []

    # Для каждого предлажения
    for sent in sentences:
        
        # Найти все слова и превезти их к нормальной форме
        words = get_words(sent.text, type=False)
        normal_words = to_normal(words)
        print(words)
        print(normal_words)
        
        # Для каждого слова в нормальной форме
        for word in normal_words:

            # Добавить в результат отношение нахождения в предложении
            dict_1 = {}
            dict_1['first'] = 'sentence'
            dict_1['relation'] = 'part_of_sentence'
            dict_1['second'] = word

            graph.append(dict_1)
            
            # Найти синсет слова
            try:
                synsets = wikiwordnet.get_synsets(word)
                synset1 = synsets[0]
                synset1.get_words()
            except IndexError:
                return {'msg': 'Something is happend wrong', 'word': words[normal_words.index(word)]}
            
            # Добавить в результат само слово
            if len(synset1.get_words()):
                for w in synset1.get_words():
                    print(w.lemma())
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'lemma'
                    dict_1['second'] = w.lemma()
                    
                    graph.append(dict_1)
            
            # Добавить в результат определение слова
            print('definition')
            if len(synsets):
                for synset in synsets:
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'definition'
                    dict_1['second'] = {w.definition() for w in synset.get_words()}
                    
                    graph.append(dict_1)
            
            # Добавить в результат гиперонимы
            print('hypernym' != 0)   
            if len(wikiwordnet.get_hypernyms(synset1)):
                for hypernym in wikiwordnet.get_hypernyms(synset1):
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'hypernym'
                    dict_1['second'] = {w.lemma() for w in hypernym.get_words()}
                    
                    graph.append(dict_1)
            
            # Добавить в результат гипонимы
            print('hyponym')
            if len(wikiwordnet.get_hyponyms(synset1)):    
                for hyponym in wikiwordnet.get_hyponyms(synset1):
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'hyponym'
                    dict_1['second'] = {w.lemma() for w in hyponym.get_words()}
                    
                    graph.append(dict_1)
    
    words.append('sentence')
    
    return {'nodes': words, 'graph': graph}

# Часть API
# Нахождение отношений между двумя словами
@app.post('/words/find_hyp')
def only_for_two_words(words: TwoWords):
    
    # Cоздать объект словоря естественного языка
    wikiwordnet = WikiWordnet()
    
    graph = []
    
    # Добавить слова в результат
    nodes = [words.word_1, words.word_2]
    normal_nodes = to_normal(nodes)
    
    # Найти синсеты слов
    synset1 = wikiwordnet.get_synsets(normal_nodes[0])[0]
    synset2 = wikiwordnet.get_synsets(normal_nodes[1])[0]
    
    # Добавить в результат все гиперонимы
    common_hypernyms = wikiwordnet.get_lowest_common_hypernyms(synset1, synset2)
    if len(common_hypernyms):
        for ch, dst1, dst2 in sorted(common_hypernyms, key=lambda x: x[1] + x[2]):
            dict_1 = {}
            dict_1['first'] = normal_nodes
            dict_1['relation'] = 'common_hypernyms'            
            dict_1['second']= {c.lemma() for c in ch.get_words()}

            graph.append(dict_1)
    
    # Добавить в результат все гипонимы
    common_hyponyms = wikiwordnet.get_lowest_common_hyponyms(synset1, synset2)
    if len(common_hyponyms):
        for ch, dst1, dst2 in sorted(common_hyponyms, key=lambda x: x[1] + x[2]):
            dict_1 = {}
            dict_1['first'] = normal_nodes
            dict_1['relation'] = 'common_hyponyms'            
            dict_1['second']= {c.lemma() for c in ch.get_words()}

            graph.append(dict_1)

    return {'nodes': nodes, 'graph': graph}