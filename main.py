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

FONT = pygame.font.SysFont('Arial', 22)
COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')


class InputBox:

    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    print(self.text)
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)



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


def button(screen, msg, x, y, w, h, ic, ac, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x+w > mouse[0] > x and y+h > mouse[1] > y:
            pygame.draw.rect(screen, ac, (x, y, w, h))
            if click[0] == 1 and action:
                action()
        else:
            pygame.draw.rect(screen, ic, (x, y, w, h))

        smallText = pygame.font.SysFont("Arial", 21)
        textSurf, textRect = text_objects(msg, smallText)
        textRect.center = ((x+(w/2)), (y+(h/2)))
        screen.blit(textSurf, textRect)


def text_objects(text, font):
        textSurface = font.render(text, True, (255, 255, 255))
        return textSurface, textSurface.get_rect()


def main():
    # Инициализируем pygame
    pygame.init()
    screen = pygame.display.set_mode((600, 480))
    get_text(screen)
    # Заводим объект, в котором будем хранить все параметры отрисовки карты.
    mp = MapParams()
    box = InputBox(50, 450, 200, 30)

    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:  # Выход из программы
            break
        elif event.type == pygame.KEYUP:  # Обрабатываем различные нажатые клавиши.
            mp.update(event)
            print(event.key)
        box.handle_event(event)
        # другие eventы

        # Загружаем карту, используя текущие параметры.
        map_file = load_map(mp)
        button(screen, 'Искать', 520, 450, 80, 30, (0, 200, 0), (0, 255, 0))
        # Рисуем картинку, загружаемую из только что созданного файла.
        screen.blit(pygame.image.load(map_file), (0, 0))
        box.update()
        box.draw(screen)
        # Переключаем экран и ждем закрытия окна.
        pygame.display.flip()

    pygame.quit()
    # Удаляем за собой файл с изображением.
    os.remove(map_file)


if __name__ == "__main__":
    main()
