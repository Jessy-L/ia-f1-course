import math
import sys
import neat
import pygame

# WIDTH = 1600
# HEIGHT = 880

WIDTH = 1920
HEIGHT = 1080

CAR_SIZE_X = 60    
CAR_SIZE_Y = 60

BORDER_COLOR = (255, 255, 255, 255) # Blanc

current_generation = 0 # Compteur de génération

class Car:

    def __init__(self):
        # Crée les 4 noeuds de sortie
        self.sprite = pygame.image.load('image/car/car.png').convert() # converti l'image en surface
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.rotated_sprite = self.sprite 

        # self.position = [690, 740] # Position de départ
        self.position = [830, 920] # Position de départ
        self.angle = 0
        self.speed = 0

        self.speed_set = False # drapeau pour savoir si la vitesse a été définie

        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2] # Calculate Center

        self.radars = [] # Liste des radars
        self.drawing_radars = [] 

        self.alive = True # boolean pour savoir si la voiture est en vie

        self.distance = 0 # distance parcourue
        self.time = 0 # temp écoulé

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position)
        self.draw_radar(screen)

    def draw_radar(self, screen):
        # Dessine tous les radars de la voiture
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 255, 0), position, 5)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:

            # Si un coin touche la couleur de la bordure -> Crash
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break

    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Boucle tant que la couleur n'est pas la couleur de la bordure et que la longueur est inférieure à 300
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Calcule la distance jusqu'à la bordure et l'ajoute à la liste des radars
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])
    
    def update(self, game_map):
        # Definit la vitesse à 20 pour la première fois
        # Seulement quand on a 4 noeuds de sortie avec accélérer et ralentir
        if not self.speed_set:
            self.speed = 20
            self.speed_set = True

        # Recupère le sprite tourné et déplacez-le dans la bonne direction X
        # Ne laisse pas la voiture aller plus près de 20px de l'arête
        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # Ecrase la distance et le temps
        self.distance += self.speed
        self.time += 1
        
        # Déplace dans la bonne direction Y
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], WIDTH - 120)

        # calcule le centre de la voiture
        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        # Calcule les quatre coins
        # La longueur est la moitié du côté
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        # Check la collision et efface les radars
        self.check_collision(game_map)
        self.radars.clear()

        # Depuis -90 à 120 avec une taille d'étape de 45 vérifiez le radar
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

    def get_data(self):
        # Recupère les distances des radars
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def is_alive(self):
        # Basiquement, si la voiture est en vie, elle est en vie
        return self.alive

    def get_reward(self):
        # calcule la récompense en fonction de la distance parcourue
        # et du temps passé
        return self.distance / (CAR_SIZE_X / 2)

    def rotate_center(self, image, angle):
        # Rotate Le Rectangle
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image


def run_simulation(genomes, config):
    
    # Vide les collections pour les réseaux et les voitures
    nets = []
    cars = []

    # initialise pygame et l'affichage
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    # pour chaque voiture, créez un réseau neuronal
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car())

    # Config de la map et element de l'interface
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 30)
    alive_font = pygame.font.SysFont("Arial", 20)
    game_map = pygame.image.load('image/map/map4.png').convert()

    global current_generation
    current_generation += 1

    counter = 0

    while True:
        # quitte le jeu si on appuie sur la croix
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # Pour chaque voiture, récupérez l'action qu'elle prend
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10 # Left
            elif choice == 1:
                car.angle -= 10 # Right
            elif choice == 2:
                if(car.speed - 2 >= 12):
                    car.speed -= 2 # Slow Down
            else:
                car.speed += 2 # Speed Up
        
        # Update La Map Et Les Voitures
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
                car.update(game_map)
                genomes[i][1].fitness += car.get_reward()

        if still_alive == 0:
            break

        counter += 1
        if counter == 30 * 40: # stoppe la simulation après 20 secondes
            break

        # Affiche La Map Et Les Voitures
        screen.blit(game_map, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(screen)
        
        # Affiche L'interface
        text = generation_font.render("Géneration : " + str(current_generation), True, (0,0,0))
        text_rect = text.get_rect()
        text_rect.center = (900, 450)
        screen.blit(text, text_rect)

        text = alive_font.render("Encore en vie : " + str(still_alive), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (900, 490)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(60) # 60 FPS

if __name__ == "__main__":
    
    # Charge Config.txt
    config_path = "./config.txt"
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    # Créer une population et ajoutez un rapporteur pour afficher les statistiques
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    # Run la simulation 1000 fois
    population.run(run_simulation, 1000)
