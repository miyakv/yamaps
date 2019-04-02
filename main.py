import pygame
import requests
import sys
import os
import math


from common.distance import lonlat_distance
from common.geocoder import geocode as reverse_geocode
from common.business import find_business

modes = ['map', 'sat', 'skl']
LAT_STEP = 0.002  # Шаги при движении карты по широте и долготе
LON_STEP = 0.005
coord_to_geo_x = 0.0000428  # Пропорции пиксельных и географических координат.
coord_to_geo_y = 0.0000428


def ll(x, y):
    return "{0},{1}".format(x, y)


class MapParams(object):
    # Параметры по умолчанию.
    def __init__(self):
        self.lat = 55.729738  # Координаты центра карты на старте.
        self.lon = 37.664777
        self.zoom = 16  # Масштаб карты на старте.
        self.mode_ind = 0
        self.type = modes[self.mode_ind]  # Тип карты на старте.
        self.k = 2 ** (15 - self.zoom)

        self.search_result = None  # Найденный объект для отображения на карте.
        self.use_postal_code = False

    # Преобразование координат в параметр ll
    def ll(self):
        return ll(self.lon, self.lat)

    def change_mode(self):
        self.mode_ind += 1
        if self.mode_ind == 3:
            self.mode_ind = 0
        self.type = modes[self.mode_ind]

    # Обновление параметров карты по нажатой клавише.
    def update(self, event):
        if event.key == 280:
            if self.zoom != 17:
                self.zoom += 1
                self.k = 2 ** (15 - self.zoom)
        elif event.key == 281:
            if self.zoom != 0:
                self.zoom -= 1
                self.k = 2 ** (15 - self.zoom)

        elif event.key == 273:
            self.lat += LAT_STEP * self.k
        elif event.key == 274:
            self.lat -= LAT_STEP * self.k
        elif event.key == 275:
            self.lon += LON_STEP * self.k
        elif event.key == 276:
            self.lon -= LON_STEP * self.k

        elif event.key == 114:
            self.change_mode()

    # Преобразование экранных координат в географические.
    def screen_to_geo(self, pos):
        dy = 225 - pos[1]
        dx = pos[0] - 300
        lx = self.lon + dx * coord_to_geo_x * math.pow(2, 15 - self.zoom)
        ly = self.lat + dy * coord_to_geo_y * math.cos(math.radians(self.lat)) * math.pow(2, 15 - self.zoom)
        return lx, ly

    # еще несколько функций


# Создание карты с соответствующими параметрами.
def load_map(mp):

    map_request = "http://static-maps.yandex.ru/1.x/?ll={}&z={}&l={}".format(mp.ll(), mp.zoom, mp.type)
    response = requests.get(map_request)

    if not response:
        print("Ошибка выполнения запроса:")
        print(map_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)

    # Запишем полученное изображение в файл.
    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)
    return map_file


def get_text(screen):
    pygame.font.init()
    myfont = pygame.font.SysFont('Arial', 20)
    text = myfont.render('Press R to change map style', True, pygame.Color("white"))
    screen.blit(text, (0, 450))


def main():
    # Инициализируем pygame
    pygame.init()
    screen = pygame.display.set_mode((600, 480))
    get_text(screen)


    # Заводим объект, в котором будем хранить все параметры отрисовки карты.
    mp = MapParams()

    while True:
        event = pygame.event.wait()

        if event.type == pygame.QUIT:  # Выход из программы
            break
        elif event.type == pygame.KEYUP:  # Обрабатываем различные нажатые клавиши.
            mp.update(event)
            print(event.key)
        # другие eventы

        # Загружаем карту, используя текущие параметры.
        map_file = load_map(mp)

        # Рисуем картинку, загружаемую из только что созданного файла.
        screen.blit(pygame.image.load(map_file), (0, 0))

        # Переключаем экран и ждем закрытия окна.
        pygame.display.flip()

    pygame.quit()
    # Удаляем за собой файл с изображением.
    os.remove(map_file)


if __name__ == "__main__":
    main()
