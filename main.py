import pygame 
import random
import pickle
import math


class tile():
    def __init__(self,position,data,orientation):
        self.position = position
        self.data = data
        self.orientation = orientation
        self.entropy = 8
        self.errored = False 

###==- WFCA -==###

def initialize(width,height):
    # Create my fictionnal table of bits, parts of cahun's face
    bits_list = []
    for i in range(width):
        bits_list.append([])
        for j in range(height):
            # Fill the table with blank tiles
            bits_list[i].append(tile((i,j),0,0))

    return bits_list

def learn_priority(data_set,parts):
    priority_table = {}
    
    #-- Cleaning data set (remove zeroes) --#
    data_table = []
    for i in range(len(data_set)):
        row = []
        # Add to the row the non-0 elements 
        for element in data_set[i]:
            if element:
                row.append(element)

        # Add to the map the row
        if row:
            data_table.append(row)


    #=- Define size of useful data -=#
    data_width = len(data_table)

    data_height = len(data_table[0])

    #=- Create the empty table of priorities -=#
    for part in parts:
        priority_table[part] = []
        #Add all the possible neighbours
        for neighbour_index in range(neighbours_amount):
            priority_table[part].append([])
            
            #For each neighbour, set 0 as default priority for all body part 
            for j in range(len(parts)):
                priority_table[part][neighbour_index].append(0)

    #=- For each element of data table associate its relative prorities -=#
                
    #Loop around each element
    for i in range(data_width):
        for j in range(data_height):
            tile_type = data_table[i][j]
            #Loop around each neighbour of the tile
            for neighbour_index in range(neighbours_amount):
                
                if not is_tile_existing(i,j,neighbours[neighbour_index],data_width,data_height):
                    continue 
                
                # Get the type of the neighbour, and its index
                neighbour_type = data_table[i+neighbours[neighbour_index][0]][j+neighbours[neighbour_index][1]]
                neighbour_type_index = parts.index(neighbour_type)
                
                # Update the priorities, in function of the part, apply a factor
                part_factor = factor if neighbour_type_index != 3 else skin_factor
                priority_table[tile_type][neighbour_index][neighbour_type_index] += 1*part_factor
    
    return priority_table

def send_tile(tiles_table):
    aimed_tile = get_least_entropic(tiles_table)

    useful_neighbours = []
    
    # Get the neighbours of the aimed tile 
    for neighbour_index,neighbour in enumerate(neighbours):
        if not is_tile_existing(*aimed_tile.position,neighbour,width,height):
            continue 
        
        # Don't get it if it isn't defined (data==0)
        neighbour_tile = tiles_table[aimed_tile.position[0]+neighbour[0]][aimed_tile.position[1]+neighbour[1]]
        if not neighbour_tile.data:
            continue 
        
        useful_neighbours.append([neighbour_tile,neighbour_index])

    return draw_part(get_intensities(useful_neighbours)),aimed_tile
  
def get_least_entropic(tiles_table): 
    # Get the table as a list 
    tiles_list = [tiles_table[i][j] for i in range(width) for j in range(height) if not tiles_table[i][j].data] 
    minimal_entropy = min(tiles_list,key=lambda x: x.entropy).entropy 
    
    # Get everytile with an entropy == minimal one 
    less_entropics = [tile  for tile in tiles_list if tile.entropy == minimal_entropy]
    
    return less_entropics[random.randint(0,len(less_entropics))-1]
  
def get_intensities(useful_neigbours):
        intensities = []
        
        for part_index in range(len(parts)):
            part_intensity = 0
            
            # If a tile is present, add the intensity of the presence 
            # Of the tile to the opposite direction by the factor of priority
            for neighbour,neighbour_index in useful_neigbours:
                part_intensity += tiles_dictionnary[neighbour.data][(neighbour_index+4)%8][part_index]

            
            intensities.append(part_intensity)
        
        return intensities

def draw_part(intensities):
    intervals = []
    inferior_bound = 0
    superior_bound = 0

    exp_sum = sum([math.exp(intensity) for intensity in intensities])    

    # Softmax distribution
    for i in range(len(intensities)):
        interval_length = math.exp(intensities[i])/exp_sum 
        superior_bound = inferior_bound + interval_length
        
        intervals.append([inferior_bound,superior_bound])
        
        inferior_bound += interval_length
        
    # Actually draw the face part
    draw_number = random.random()
    for i in range(len(intervals)):
        if intervals[i][0]<= draw_number < intervals[i][1]:
            return i

def modify_tile(tiles_table,tile_infos):
    tiles_table[tile_infos[1].position[0]][tile_infos[1].position[1]].data = parts[tile_infos[0]]
    
    update_entropy(tiles_table,tile_infos[1].position[0],tile_infos[1].position[1])
    return tiles_table

def update_entropy(tiles_table,x,y):
    for neighbour in neighbours:
        if not is_tile_existing(x,y,neighbour,width,height):
            continue 
        
        tiles_table[x+neighbour[0]][y+neighbour[1]].entropy -= 1

def get_neighbours(accuracy):
    values = []
    orientations= [0,-1,0,1]

    base_value = [accuracy,accuracy]
    for k in range(4):
        for h in range(accuracy*2):
            
            values.append(base_value.copy())
            base_value[0] += orientations[k]
            base_value[1] += orientations[(k+1)%4]

    first_values = values[0:accuracy]

    for value in first_values:
        values.remove(value)
        values.append(value)
    return values

def is_tile_existing(i,j,neighbour,width,height):
    return i + neighbour[0] >=0 and i + neighbour[0] < width and j + neighbour[1] >= 0 and j + neighbour[1] < height

def load_data_set():
    with open('cahun.data', 'rb') as f:
        d = pickle.load(f)
    return d 


width =16
height = 16

accuracy = 1
skin_factor = 1
factor = 1.507 # How much non-skin if favorised
parts = ["eye","mouth","nose","skin","leftEar","rightEar"]

neighbours = get_neighbours(accuracy)
neighbours_amount = len(neighbours)
tiles_dictionnary = learn_priority(load_data_set(),parts)
tiles_canva = initialize(width,height)

###==- Decoration -==###

def get_empty_position(tiles_table,taken):
    blanks = []
    for i in range(width):
        for j in range(height):
            if tiles_table[i][j].data in ["skin"]:
                is_in = False 
                for take in taken:
                    if [i,j]==take:
                        is_in = True
                if not is_in:
                    blanks.append([i,j])
                    
    if len(blanks):
        position = blanks[random.randint(0,len(blanks))-1]
    else:
        position = None
    return position

def load_images():
    background=  pygame.transform.scale(pygame.transform.scale(pygame.image.load("background.png"), (width,height)), (screen_width,screen_width))
    images = {}
    base_images = {}
    for face_part in parts:
        images[face_part] = pygame.transform.scale(pygame.image.load(face_part+"Rectified.png"), size_of_cell)
        base_images[face_part] = pygame.transform.scale(pygame.image.load(face_part+"Rectified.png"), size_of_cell)

    return images,base_images,background

def set_up_letters():
    cooldowns = []
    letter_position = []
    letter_offset = []

    for i in range(len(text)):
        letter_offset.append([(size_of_cell[0]-font.size(text[i])[0])/2,(size_of_cell[1]-font.size(text[i])[1])/2])
        letter_position.append(None)
        cooldowns.append(random.randint(0,800))
    
    return cooldowns,letter_position,letter_offset

def switch_images():
    global switch_state, images
    switch_state = (1+switch_state)%3
    images["eye"] = pygame.transform.rotate(pygame.transform.scale(base_images[parts[(0+switch_state)%3]], size_of_cell),angle)
    images["mouth"] = pygame.transform.rotate(pygame.transform.scale(base_images[parts[(1+switch_state)%3]], size_of_cell),angle)
    images["nose"] = pygame.transform.rotate(pygame.transform.scale(base_images[parts[(2+switch_state)%3]], size_of_cell),angle)

def rotate_images():
    angle = (angle+90)%360
    for face_part in parts:
        if face_part in ["eye","mouth","nose"]:
            images[face_part] = pygame.transform.rotate(pygame.transform.scale(base_images[parts[(["eye","mouth","nose"].index(face_part)+switch_state)%3]], size_of_cell),angle)
        else:
            images[face_part] = pygame.transform.rotate(pygame.transform.scale(base_images[face_part], size_of_cell),angle)

def update_letters():
    global cooldowns, letter_position
    for i in range(len(cooldowns)):
        cooldowns[i] += 1
        if cooldowns[i] > 800: # cooldown max value
            cooldowns[i] = 0

            letter_position[i] = get_empty_position(tiles_canva,letter_position)
            

# Actual pygame stuff
            
pygame.font.init()
clock = pygame.time.Clock()
running = True 
screen_width = 720 # multiple of 16
size_of_cell = int(screen_width/width),int(screen_width/height)
screen = pygame.display.set_mode((screen_width,screen_width))
pygame.display.set_caption("Cahunorganised Chaos")

# Font managing
font_color_difference = 5
font = pygame.font.Font("BFranklin.ttf",int(0.04*screen_width))
text ="Aveuxnonavenus&Ewann"
cooldowns, letter_position, letter_offset = set_up_letters()

images,base_images,background = load_images()

# Cosmetic

flippers = ["eye","mouth","nose"]
switch_state = 0 
angle = 0
scrolling = [0,0]

generating = 0 # while the canva isn't fully filled, fill it 


while running:
    # Update everything #
    
    # Actually call the WFCA functions

    if generating < width*height:
        generating +=1
        tiles_canva = modify_tile(tiles_canva,send_tile(tiles_canva))
    
    update_letters()
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 
        if event.type == pygame.KEYDOWN:  
            if event.key == pygame.K_RETURN:
                rotate_images()            
            if event.key == pygame.K_SPACE:
                switch_images()
    
    # Draw letters and face parts #
                
    screen.blit(background,(0,0))

    for i in range(width):
        for j in range(height):

            if not tiles_canva[i][j].data:
                continue 
            
            screen.blit(images[tiles_canva[i][j].data],(((i-scrolling[0])%width)*size_of_cell[0],((j+scrolling[1])%height)*size_of_cell[1]))
            
            for n,letter_pos in enumerate(letter_position):
                if [i,j] == letter_pos:
                    screen.blit(font.render(text[n],True,(197-font_color_difference,191-font_color_difference,177-font_color_difference)),(((i-scrolling[0])%width)*size_of_cell[0]+letter_offset[n][0],((j+scrolling[1])%height)*size_of_cell[1]+letter_offset[n][1]))

    pygame.display.flip()
